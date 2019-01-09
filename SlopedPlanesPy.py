# -*- coding: utf8 -*-
# *****************************************************************************
# *                                                                           *
# *    Copyright (c) 2017                                                     *
# *                                                                           *
# *    This program is free software; you can redistribute it and/or modify   *
# *    it under the terms of the GNU Lesser General Public License (LGPL)     *
# *    as published by the Free Software Foundation; either version 2 of      *
# *    the License, or (at your option) any later version.                    *
# *    For detail see the LICENSE text file.                                  *
# *                                                                           *
# *    This program is distributed in the hope that it will be useful,        *
# *    but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                   *
# *    See the  GNU Library General Public License for more details.          *
# *                                                                           *
# *    You should have received a copy of the GNU Library General Public      *
# *    License along with this program; if not, write to the Free Software    *
# *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307   *
# *    USA                                                                    *
# *                                                                           *
# *****************************************************************************


import math
import FreeCAD
import Part
import Sketcher
if FreeCAD.GuiUp:
    import FreeCADGui


__title__ = "SlopedPlanes Macro"
__author__ = "Damian Caceres Moreno"
__url__ = "http://www.freecadweb.org"
__version__ = ""


V = FreeCAD.Vector
origin = V(0, 0, 0)


class _Py(object):

    '''A functional Class bequeaths methods and class variables'''

    tolerance = 1e-7
    precision = 1e7
    reverse = False
    size = 0
    normal = V(0, 0, 1)
    face = None
    pyFace = None
    slopedPlanes = None
    upList = []

    def addValue(self, prop, value, direction='forward'):

        '''addValue(self, prop, value, direction='forward')'''
        # podría necesitar una protección para cuando ya esta rellena la propiedad
        valueList = getattr(self, prop)
        if direction == 'forward':
            valueList.insert(0, value)
        else:
            valueList.append(value)
        setattr(self, prop, valueList)

    def selectAlignmentBase(self):

        '''selectAlignmentBase(self)
        selects an unique alignment which base plane is (numWire, numGeom),
        and return it, or None.'''

        for pyAlign in self.alignedList:
            if pyAlign.base == self:
                return pyAlign

        return None

    def selectReflex(self, nGeom):

        '''selectReflex(self, nGeom)
        selects an unique reflex corner in the wire numWire,
        which envolves the planes numGeom and nGeom,
        and return it, or None.'''

        for pyReflex in self.reflexedList:
            for pyPlane in pyReflex.planes:
                if nGeom == pyPlane.numGeom:
                    return pyReflex

        return None

    def selectPlane(self, numWire, numGeom, pyFace=None):

        '''selectPlane(self, numWire, numGeom, pyFace=None)
        Selects the plane numWire and numGeom.'''

        if not pyFace:
            pyFace = _Py.pyFace

        return pyFace.wires[numWire].planes[numGeom]

    def selectBasePlane(self, numWire, numGeom):

        '''selectBasePlane(self, numWire, numGeom)
        Selects the plane numWire and numGeom, or if this lacks of shape
        selects the base plane of the alignment.'''

        pyPlane = self.selectPlane(numWire, numGeom)

        if not pyPlane.geomAligned:
            [nW, nG] = pyPlane.angle
            pyPlane = self.selectPlane(nW, nG)

        return pyPlane

    def cutting(self, cutted, cutter, geomShape):

        '''cutting(self, cutted, cutter, geomShape)'''

        cutted = cutted.cut(cutter, _Py.tolerance)
        cutted = self.selectFace(cutted.Faces, geomShape)

        # except FreeCAD.Base.FreeCADError:
        # except Part.OCCError:

        return cutted

    def cuttingPyth(self, cutter):

        '''cuttingPyth(self, cutter)'''

        cutted = self.shape
        if cutted:
            geomShape = self.geomShape
            cutted = self.cutting(cutted, cutter, geomShape)
            self.shape = cutted

        return cutted

    def selectFace(self, faceList, geomShape):

        '''selectFace(self, faceList, geomShape)'''

        for face in faceList:
            section = face.section([geomShape], _Py.tolerance)
            if section.Edges:
                return face

        # OCCT bug
        if faceList:
            return faceList[0]

        return None

    def selectFacePoint(self, shape, point):

        '''selectFacePoint(self, shape, point)'''

        vertex = Part.Vertex(point)
        for ff in shape.Faces:
            section = vertex.section([ff], _Py.tolerance)
            if section.Vertexes:
                return ff

    def selectShape(self, big=False):

        '''selectShape(self)'''

        if self.aligned:
            # print 'a'
            aliList = self.alignedList
            shape = []
            for pyA in aliList:
                shape.extend(pyA.simulatedAlignment)
            shape = Part.makeCompound(shape)

        elif self.reflexed:
            # print 'b'
            if big:
                shape = self.bigShape
            else:
                shape = self.simulatedShape

        else:
            # print 'c'
            if big:
                shape = self.bigShape
            else:
                shape = self.shape

        return shape

    def printSummary(self):

        '''printSummary(self)'''
        pass

        # print '###############################################################'

        # print '********* wires ', _Py.pyFace.wires
        # for pyWire in _Py.pyFace.wires:

        #     print '****** numWire ', pyWire.numWire
        #     # print '*** coordinates ', pyWire.coordinates
        #     # print '*** wire ', [e.Point for e in pyWire.wire.OrderedVertexes]
        #     print '*** reflexs ', pyWire.reflexs
        #     for pyReflex in pyWire.reflexs:

        #         print 'planes ', pyReflex.planes
        #         print 'rangoInter ', pyReflex.rango
        #         print 'rear reflex', pyReflex.rear

        #         for pyPlane in pyReflex.planes:
        #             print 'numGeom ', pyPlane.numGeom  # , pyPlane.reflexedList
        #             print 'rear plane ', pyPlane.rear
        #             print 'secondRear ', pyPlane.secondRear
        #             print 'rango ', pyPlane.rango
        #             '''forward = pyPlane.forward
        #             print 'forward ',\
        #                 (self.roundVector(forward.firstVertex(True).Point),
        #                  self.roundVector(forward.lastVertex(True).Point),
        #                  forward.Curve)
        #             backward = pyPlane.backward
        #             print 'backward ',\
        #                 (self.roundVector(backward.firstVertex(True).Point),
        #                  self.roundVector(backward.lastVertex(True).Point),
        #                  backward.Curve)'''
        #             print '#########'

        #         print '#######################'

        # print '********* alignments ', _Py.pyFace.alignments
        # for pyAlignment in _Py.pyFace.alignments:

        #     print '****** base'
        #     print(pyAlignment.base.numWire, pyAlignment.base.numGeom), pyAlignment.base.alignedList
        #     print 'angle ', pyAlignment.base.angle
        #     print 'rear ', pyAlignment.rear
        #     print 'rear base', pyAlignment.base.rear
        #     print 'rango ', pyAlignment.base.rango
        #     # print 'geom ', pyAlignment.base.geom
        #     # print 'geomAligned ', pyAlignment.base.geomAligned
        #     # print 'shape ', pyAlignment.base.shape
        #     print 'falsify ', pyAlignment.falsify
        #     print 'virtualized ', pyAlignment.base.virtualized
        #     print 'cross ', pyAlignment.base.cross
        #     print 'rangoChop ', pyAlignment.rango
        #     print 'rangoRear ', pyAlignment.rangoRear
        #     print 'prior ', (pyAlignment.prior.numWire, pyAlignment.prior.numGeom)
        #     print 'later ', (pyAlignment.later.numWire, pyAlignment.later.numGeom)

        #     print '*** chops ', [[(x.numWire, x.numGeom),
        #                           (y.numWire, y.numGeom)]
        #                          for [x, y] in pyAlignment.chops]
        #     for chop in pyAlignment.chops:
        #         for pyPlane in chop:
        #             print(pyPlane.numWire, pyPlane.numGeom), pyPlane.chopedList
        #             print 'rear ', pyPlane.rear
        #             print 'secondRear ', pyPlane.secondRear
        #             print 'rango ', pyPlane.rango
        #             print 'virtualized ', pyPlane.virtualized
        #             print 'cross ', pyPlane.cross

        #     print '*** aligns ', [(x.numWire, x.numGeom) for x in pyAlignment.aligns]
        #     for align in pyAlignment.aligns:
        #         print(align.numWire, align.numGeom), align.alignedList
        #         print 'rear ', align.rear
        #         print 'secondRear ', align.secondRear
        #         print 'rango ', align.rango
        #         print 'angle ', align.angle
        #         print 'virtualized ', align.virtualized
        #         print 'cross ', align.cross
        #         # print 'geom ', align.geom
        #         # print 'geomAligned ', align.geomAligned
        #         # print 'shape ', align.shape

        # print '###############################################################'

    def printSerialSummary(self):

        '''printSerialSummary(self)'''

        for pyFace in self.Pyth:
            for pyWire in pyFace.wires:
                for pyPlane in pyWire.planes:
                    pyPlane.printPlaneSummary()

    def printPlaneSummary(self):

        '''printPlaneSummary(self)'''
        pass

        # print '###### ', (self.numWire, self.numGeom), self.shape
        # if self.shape:
        #     print 'Area ', self.shape.Area
        # geom = self.geomShape
        # print (self.roundVector(geom.firstVertex(True).Point), self.roundVector(geom.lastVertex(True).Point))
        # forward = self.forward
        # try:
        #     print (self.roundVector(forward.firstVertex(True).Point), self.roundVector(forward.lastVertex(True).Point))
        # except:
        #     pass
        # backward = self.backward
        # try:
        #     print (self.roundVector(backward.firstVertex(True).Point), self.roundVector(backward.lastVertex(True).Point))
        # except:
        #     pass

        # print '######'

    def printAssociatedShapes(self, numWire, numGeom):

        '''printAssociatedShapes(self, numWire, numGeom)'''

        slopedPlanes = self.slopedPlanes
        sketch = slopedPlanes.Base

        pl = sketch.Placement
        place = slopedPlanes.Placement
        placement = pl.multiply(place)

        pyPlane = self.selectPlane(numWire, numGeom)

        shape = pyPlane.shape
        if shape:

            shape.Placement = placement
            Part.show(shape, slopedPlanes.Name+' shape '+str(numWire)+' '+str(numGeom))

        simulatedShape = pyPlane.simulatedShape
        if simulatedShape:

            simulatedShape.Placement = placement
            Part.show(simulatedShape, slopedPlanes.Name+' simulatedShape '+str(numWire)+' '+str(numGeom))

        cutter = pyPlane.cutter
        if cutter:

            compound = Part.makeCompound(cutter)
            compound.Placement = placement
            Part.show(compound, slopedPlanes.Name+' cutter '+str(numWire)+' '+str(numGeom))

        under = pyPlane.under
        if under:

            compound = Part.makeCompound(under)
            compound.Placement = placement
            Part.show(compound, slopedPlanes.Name+' under '+str(numWire)+' '+str(numGeom))

        seed = pyPlane.seed
        if seed:

            compound = Part.makeCompound(seed)
            compound.Placement = placement
            Part.show(compound, slopedPlanes.Name+' seed '+str(numWire)+' '+str(numGeom))

        if pyPlane.aligned:
            pyAli = pyPlane.selectAlignmentBase()
            if pyAli:

                compound = Part.makeCompound(pyAli.simulatedAlignment)
                compound.Placement = placement
                Part.show(compound, slopedPlanes.Name+' simulatedAlignment '+str(numWire)+' '+str(numGeom))

        try:
            forward = pyPlane.forward
            forward.Placement = placement
            backward = pyPlane.backward
            backward.Placement = placement
            Part.show(forward, slopedPlanes.Name+' forward '+str(numWire)+' '+str(numGeom))
            Part.show(backward, slopedPlanes.Name+' backward '+str(numWire)+' '+str(numGeom))
        except AttributeError:
            pass

        try:
            gS = pyPlane.geomShape
            gS.Placement = placement
            Part.show(gS, slopedPlanes.Name+' gS '+str(numWire)+' '+str(numGeom))
        except AttributeError:
            pass

        virtuals = pyPlane.virtuals
        if virtuals:
            for pyP in virtuals:

                shape = pyP.shape
                if shape:

                    shape.Placement = placement
                    Part.show(shape, slopedPlanes.Name+' virtual shape '+str(numWire)+' '+str(numGeom))

                simulatedShape = pyP.simulatedShape
                if simulatedShape:

                    simulatedShape.Placement = placement
                    Part.show(simulatedShape, slopedPlanes.Name+'virtual simulatedShape '+str(numWire)+' '+str(numGeom))

                if pyP.aligned:
                    pyAli = pyP.selectAlignmentBase()
                    if pyAli:

                        compound = Part.makeCompound(pyAli.simulatedAlignment)
                        compound.Placement = placement
                        Part.show(compound, slopedPlanes.Name+'virtual simulatedAlignment '+str(numWire)+' '+str(numGeom))

                under = pyP.under
                if under:

                    compound = Part.makeCompound(pyP.under)
                    compound.Placement = placement
                    Part.show(compound, slopedPlanes.Name+' virtual under '+str(numWire)+' '+str(numGeom))

                cutter = pyP.cutter
                if cutter:

                    cero = FreeCAD.Placement()  # no se en que momento se desplazan con el sketch

                    for ff in cutter:
                        ff.Placement = cero

                    compound = Part.makeCompound(cutter)
                    compound.Placement = placement
                    Part.show(compound, slopedPlanes.Name+' cutter '+str(numWire)+' '+str(numGeom))

    def printControl(self, text):

        '''printControl(self, text)'''

        pass

        # print '###############################################################'

        # print text

        # for pyWire in _Py.pyFace.wires:
        #     print 'wire ', pyWire.numWire
        #     for pyPlane in pyWire.planes:
        #         print pyPlane.numGeom, pyPlane.control

        # print '###############################################################'

    def convexReflex(self, eje, nextEje):

        '''convexReflex(self, eje, nextEje)'''

        cross = eje.cross(nextEje)
        corner = None
        if cross != origin:
            cross.normalize()

            if cross == _Py.normal:
                corner = 'convex'
            else:
                corner = 'reflex'

        return corner

    def sliceIndex(self, index, lenWire):

        '''sliceIndex(self, index, lenWire)'''

        if index >= lenWire:
            index = index - lenWire

        elif index < 0:
            index = index + lenWire

        return index

    def roundVector(self, vector):

        '''roundVector(self, vector)'''

        precision = _Py.precision

        return V(round(vector.x, precision),
                 round(vector.y, precision),
                 round(vector.z, precision))

    def rotateVector(self, vector, axis, angle):

        '''rotateVector(self, vector, axis, angle)'''

        rotation = FreeCAD.Rotation(axis, angle)
        placement = FreeCAD.Placement(origin, rotation)
        return placement.multVec(vector)

    def faceNormal(self, face):

        '''faceNormal(self, face)'''

        return self.roundVector(face.normalAt(0, 0))

    def faceDatas(self, face):

        '''faceDatas(self, face)'''

        # print '###### faceDatas'

        normal = self.faceNormal(face)

        wire = face.OuterWire

        orderVert = wire.OrderedVertexes
        orderPoint = [vert.Point for vert in orderVert]

        if len(orderVert) == 1:
            # print 'closed'

            curve = wire.Edges[0].Curve
            startParam = 0
            endParam = 2 * math.pi
            geom = self.makeGeom(curve, startParam, endParam)
            geometryList = [geom]

        else:
            # print 'no closed'

            geometryList = self.geometries(face, orderPoint)

        coordinates = [self.roundVector(point) for point in orderPoint]

        if normal == _Py.normal:
            index = self.lowerLeftPoint(coordinates)
        else:
            index = self.upperLeftPoint(coordinates)

        coordinates = coordinates[index:] + coordinates[:index]
        geometryList = geometryList[index:] + geometryList[:index]

        # print coordinates, geometryList

        return coordinates, geometryList

    def upperLeftPoint(self, coordinates):

        '''upperLeftPoint(self, coordinates)'''

        orig = coordinates[0]
        n = -1
        for col in coordinates:
            n += 1
            if col.y > orig.y:
                orig = col
            elif col.y == orig.y:
                if col.x < orig.x:
                    orig = col
        return coordinates.index(orig)

    def lowerLeftPoint(self, coordinates):

        '''lowerLeftPoint(self, coordinates)'''

        orig = coordinates[0]
        n = -1
        for col in coordinates:
            n += 1
            if col.y < orig.y:
                orig = col
            elif col.y == orig.y:
                if col.x < orig.x:
                    orig = col
        return coordinates.index(orig)

    def geometries(self, face, coordinates):

        '''geometries(self, face, coordinates)'''

        # print '###### geometries'

        if len(coordinates) == 0:
            edge = face.OuterWire.Edges[0]
            return [edge.Curve]

        coordinates.append(coordinates[0])
        first = coordinates[0]
        second = coordinates[1]
        edgeList = face.OuterWire.OrderedEdges

        number = -1
        for edge in edgeList:
            number += 1
            start = edge.Vertexes[0].Point
            if start == first or start == second:
                end = edge.Vertexes[1].Point
                if end == first or end == second:
                    break
        edgeList = edgeList[number:] + edgeList[:number]

        geometries = []

        for edge, second in zip(edgeList, coordinates[1:]):

            curve = edge.Curve

            if not isinstance(curve, Part.Line):

                if edge.firstVertex(True).Point !=\
                   edge.firstVertex(False).Point:

                    curve.Axis = V(0, 0, -1)

            startParam = curve.parameter(first)
            endParam = curve.parameter(second)

            geom = self.makeGeom(curve, startParam, endParam)

            geometries.append(geom)

            first = second

        coordinates.pop()

        return geometries

    def makeGeom(self, curve, startParam, endParam):

        '''makeGeom(self, curve, startParam, endParam)'''

        # print '###### makeGeom'

        if isinstance(curve, (Part.Line, Part.LineSegment)):
            # print '1'
            geom = Part.LineSegment(curve, startParam, endParam)

        elif isinstance(curve, Part.Circle):
            # print '2'
            angleXU = curve.AngleXU
            geom = Part.ArcOfCircle(curve, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.ArcOfCircle):
            # print '3'
            angleXU = curve.AngleXU
            geom = Part.ArcOfCircle(curve.Circle, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.Ellipse):
            # print '4'
            angleXU = curve.AngleXU
            geom = Part.ArcOfEllipse(curve, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.ArcOfEllipse):
            # print '5'
            angleXU = curve.AngleXU
            geom = Part.ArcOfEllipse(curve.Ellipse, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.Parabola):
            # print '6'
            angleXU = curve.AngleXU
            geom = Part.ArcOfParabola(curve, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.ArcOfParabola):
            # print '7'
            angleXU = curve.AngleXU
            geom = Part.ArcOfParabola(curve.Parabola, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.Hyperbola):
            # print '8'
            angleXU = curve.AngleXU
            geom = Part.ArcOfHyperbola(curve, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.ArcOfHyperbola):
            # print '9'
            angleXU = curve.AngleXU
            geom = Part.ArcOfHyperbola(curve.Hyperbola, startParam, endParam)
            geom.AngleXU = angleXU

        elif isinstance(curve, Part.BSplineCurve):
            # print '10'
            pass

        # print 'geom ', geom

        return geom

    def doGeom(self):

        '''doGeom(self)'''

        # print '###### doGeom'

        if not self.aligned:
            if self.geom:
                return self.geom

        geomAligned = self.geomAligned
        curve = geomAligned.Curve
        startParam = geomAligned.parameterAt(geomAligned.firstVertex(True))
        endParam = geomAligned.parameterAt(geomAligned.lastVertex(True))
        geom = self.makeGeom(curve, startParam, endParam)

        if not self.aligned:
            self.geom = geom

        return geom

    def rang(self, pyWire, numGeom, nGeom, direction, reflex=False):

        '''rang(self, pyWire, numGeom, nGeom, direction, reflex=False)'''

        # print 'rang ', (numGeom, nGeom, reflex)

        if numGeom == nGeom:
            return []

        lenWire = len(pyWire.planes)

        if direction == 'forward':
            # print 'A'
            if reflex:
                # print 'reflex'
                num = numGeom + 2
            else:
                # print 'no reflex'
                num = numGeom + 1
            num = self.sliceIndex(num, lenWire)
            # print 'num ', num

            if nGeom >= num:
                # print 'A1'
                ran = range(num, nGeom)
            else:
                # print 'A2'
                ran = range(num, lenWire) + range(0, nGeom)

        else:
            # print 'B'
            if reflex:
                # print 'reflex'
                num = numGeom - 1
                num = self.sliceIndex(num, lenWire)
            else:
                # print 'no reflex'
                num = numGeom
            # print 'num ', num

            if numGeom >= nGeom:
                # print 'B1'
                ran = range(nGeom + 1, num)
                ran.reverse()
            else:
                # print 'B2'
                ranA = range(nGeom + 1, lenWire)
                ranA.reverse()
                ranB = range(0, num)
                ranB.reverse()
                ran = ranB + ranA

        # print 'ran ', ran
        return ran

    def makeSweepSketch(self, slopedPlanes):

        '''makeSweepSketch(self, slopedPlanes)'''

        pySketch =\
            FreeCAD.ActiveDocument.addObject('Sketcher::SketchObjectPython',
                                             'SweepSketch')

        _PySketch(pySketch)
        _ViewProviderPySketch(pySketch.ViewObject)

        pySketch.Proxy.locate(pySketch, self, slopedPlanes)
        pySketch.Proxy.slope(pySketch, self)

        linkList = slopedPlanes.SweepCurves
        linkList.append(pySketch)
        slopedPlanes.SweepCurves = linkList

        if FreeCAD.GuiUp:
            slopedPlanes.ViewObject.Proxy.task.reject()
            FreeCADGui.activeDocument().setEdit(pySketch.Name)

        self.sweepCurve = pySketch.Name

        return pySketch


class _PySketch(_Py):

    ''''''

    def __init__(self, sketch):

        '''__init__(self, sketch)'''

        sketch.Proxy = self
        self.Type = "SweepSketch"

        vectorA = V(-707.107, -707.107, 0)
        vectorB = V(0, 0, 0)
        vectorC = V(1414.21, 1414.21, 0)

        lineA = Part.LineSegment(vectorA, vectorB)
        lineA.Construction = True
        lineB = Part.LineSegment(vectorA, vectorC)
        lineB.Construction = True

        sketch.Geometry = [lineA, lineB]

        constrA = Sketcher.Constraint('Coincident', 0, 2, 1, 1)

        constrB = Sketcher.Constraint('Coincident', 0, 2, -1, 1)

        constrC = Sketcher.Constraint('Parallel', 0, 1)

        constrD = Sketcher.Constraint('Angle', -1, 1, 1, 1, 0.785398)

        sketch.Constraints = [constrA, constrB, constrC, constrD]

    def execute(self, sketch):

        '''execute(self, sketch)'''

        sketch.recompute()

    def __getstate__(self):

        '''__getstate__(self)'''

        state = dict()
        state['Type'] = self.Type
        return state

    def __setstate__(self, state):

        '''__setstate__(self, state)'''

        self.Type = state['Type']

    def locate(self, sketch, plane, slopedPlanes):

        '''locate(self, sketch, plane, slopedPlanes)'''

        numWire = plane.numWire
        geomShape = plane.geomShape
        ffPoint = geomShape.firstVertex(True).Point
        llPoint = geomShape.lastVertex(True).Point

        # print 'ffPoint ', ffPoint
        # print 'llPoint ', llPoint

        if ffPoint == llPoint:
            # print 'a'
            edge = slopedPlanes.Shape.Edges[1]
            aa = ffPoint
            bb = edge.firstVertex(True).Point
            direction = bb.sub(aa)

        else:
            # print 'b'
            direction = llPoint.sub(ffPoint)

        # print 'direction ', direction

        angle = direction.getAngle(V(1, 0, 0)) + math.pi / 2
        # print 'angle ', angle

        if ffPoint.y > llPoint.y:
            angle = angle + math.pi
            # print 'angle ', angle

        rotation = FreeCAD.Rotation()
        rotation.Axis = V(1, 0, 0)
        rotation.Angle = math.pi / 2
        sketch.Placement.Rotation = rotation

        if ffPoint == llPoint:
            # print 'aa'
            rotation = FreeCAD.Rotation()
            rotation.Axis = V(0, 0, 1)
            angleXU = geomShape.Curve.AngleXU
            # print angleXU
            if numWire == 0:
                rotation.Angle = math.pi + angleXU
            else:
                rotation.Angle = angleXU
            sketch.Placement.Rotation =\
                rotation.multiply(sketch.Placement.Rotation)

        else:
            # print 'bb'
            rotation = FreeCAD.Rotation()
            rotation.Axis = _Py.normal
            rotation.Angle = angle
            sketch.Placement.Rotation =\
                rotation.multiply(sketch.Placement.Rotation)

        sketch.Placement.Base = ffPoint

        baseSketch = slopedPlanes.Base
        placement = baseSketch.Placement

        sketch.Placement = placement.multiply(sketch.Placement)

        placement = slopedPlanes.Placement

        sketch.Placement = placement.multiply(sketch.Placement)

    def slope(self, sketch, plane):

        '''slope(self, sketch, plane)'''

        angle = plane.angle
        sketch.setDatum(3, math.radians(angle))


class _ViewProviderPySketch():

    ''''''

    def __init__(self, vobj):

        '''__init__(self, vobj)'''

        vobj.Proxy = self