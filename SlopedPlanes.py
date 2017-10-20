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
import FreeCADGui
import Part
import SlopedPlanesUtils as utils
import SlopedPlanesTaskPanel
import SlopedPlanesCommand
import SlopedPlanesPyFace
import SlopedPlanesPyWire
import SlopedPlanesPyPlane


__title__ = "SlopedPlanes Macro"
__author__ = "Damian Caceres Moreno"
__url__ = "http://www.freecadweb.org"


def makeSlopedPlanes(sketch):

    ''''''

    if sketch.TypeId != "Sketcher::SketchObject":
        return

    slopedPlanes =\
        FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "SlopedPlanes")
    _SlopedPlanes(slopedPlanes)
    _ViewProvider_SlopedPlanes(slopedPlanes.ViewObject)
    slopedPlanes.Base = sketch

    return slopedPlanes


class _SlopedPlanes():

    ''''''

    def __init__(self, slopedPlanes):

        ''''''

        slopedPlanes.addProperty("App::PropertyLink", "Base",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyBool", "Complement",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyBool", "Reverse",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyBool", "Solid",
                                 "SlopedPlanes")
        # slopedPlanes.addProperty("App::PropertyFloat", "Cap",
        # "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyFloatList", "Slopes",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyFloat", "SlopeGlobal",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyFloat", "FactorLength",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyFloat", "FactorWidth",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyPrecision", "Tolerance",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyPythonObject", "Test",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("Part::PropertyShapeHistory", "TestShape",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyPythonObject", "Step",
                                 "SlopedPlanes")
        slopedPlanes.addProperty("App::PropertyString", "Tag",
                                 "SlopedPlanes")

        slopedPlanes.Slopes = []
        slopedPlanes.SlopeGlobal = 45.0
        slopedPlanes.FactorWidth = 1
        slopedPlanes.FactorLength = 2
        # slopedPlanes.Cap = 0
        slopedPlanes.Tolerance = (1e-7, 1e-7, 1, 1e-7)
        slopedPlanes.Test = False
        slopedPlanes.Step = 15
        self.Pyth = []
        self.State = False

        slopedPlanes.Proxy = self
        self.Type = "SlopedPlanes"

    def execute(self, slopedPlanes):

        ''''''

        sketch = slopedPlanes.Base
        shape = sketch.Shape.copy()
        sketchBase = sketch.Placement.Base
        sketchAxis = sketch.Placement.Rotation.Axis
        sketchAngle = sketch.Placement.Rotation.Angle
        shape.Placement = FreeCAD.Placement()

        face = Part.makeFace(shape, "Part::FaceMakerBullseye")

        tolerance = slopedPlanes.Tolerance
        reverse = slopedPlanes.Reverse
        slope = slopedPlanes.SlopeGlobal
        width = slopedPlanes.FactorWidth
        length = slopedPlanes.FactorLength

        step = slopedPlanes.Step

        pyFaceList = self.Pyth
        # print pyFaceList
        lenPyList = len(pyFaceList)

        faceList = face.Faces
        # print faceList
        lenList = len(faceList)

        num = lenPyList - lenList
        if num > 0:
            pyFaceList = pyFaceList[:lenList]
            # print pyFaceList

        normal = utils.faceNormal(faceList[0], tolerance)

        numFace = -1
        for face in faceList:
            numFace += 1
            size = face.BoundBox.DiagonalLength

            try:
                pyFace = pyFaceList[numFace]
                # print 'a ', numFace
            except IndexError:
                pyFace = SlopedPlanesPyFace._Face(numFace)
                pyFaceList.append(pyFace)
                # print 'b ', numFace

            pyWireList = pyFace.wires
            # print pyWireList
            lenPyList = len(pyWireList)

            wireList = face.Wires
            # print wireList
            lenList = len(wireList)

            num = lenPyList - lenList
            if num > 0:
                pyWireList = pyWireList[:lenList]
                # print pyWireList

            numWire = -1
            for wire in wireList:
                numWire += 1

                try:
                    pyWire = pyWireList[numWire]
                    # print 'aa ', numWire
                except IndexError:
                    pyWire = SlopedPlanesPyWire._Wire(numWire)
                    pyWireList.append(pyWire)
                    # print 'bb ', numWire

                coordinates, geomWire, shapeGeomWire =\
                    utils.wireGeometries(wire, tolerance)

                pyWire.shapeGeom = shapeGeomWire
                coordinates.extend(coordinates[0:2])

                oldCoordinates = pyWire.coordinates
                # print oldCoordinates
                # print coordinates
                if oldCoordinates != coordinates:
                    # print 'a'
                    pyFace.reset = True
                    if len(oldCoordinates) != len(coordinates):
                        # print 'b'
                        pyWire.reset = True
                    elif oldCoordinates[0] != coordinates[0]:
                        # print 'c'
                        pyWire.reset = True

                pyWire.coordinates = coordinates

                pyPlaneList = pyWire.planes
                # print pyPlaneList
                lenPyList = len(pyPlaneList)

                planeList = wire.Edges
                # print planeList
                lenList = len(planeList)

                num = lenPyList - lenList
                if num > 0:
                    pyPlaneList = pyPlaneList[:lenList]
                    # print pyPlaneList

                numGeom = -1
                for geom in geomWire:
                    numGeom += 1

                    try:
                        pyPlane = pyPlaneList[numGeom]
                        if pyFace.reset:
                            pyPlane = SlopedPlanesPyPlane._Plane(numWire,
                                                                 numGeom)
                            pyPlaneList[numGeom] = pyPlane
                        elif pyWire.reset:
                            pyPlane.angle = slope
                            pyPlane.width = [width, width]
                            pyPlane.length = length
                    except IndexError:
                        pyPlane = SlopedPlanesPyPlane._Plane(numWire,
                                                             numGeom)
                        pyPlaneList.append(pyPlane)

                    pyPlane.geom = geom
                    pyPlane.geomAligned = geom

                pyWire.planes = pyPlaneList

            pyFace.wires = pyWireList

            if step >= 1:

                pyFace.parsing(normal, size, tolerance)

            if step >= 2:

                pyFace.planning(normal, size, reverse)

            if step >= 3:

                pyFace.trimming(tolerance)

            if step >= 4:

                pyFace.priorLater(tolerance)

            if step >= 5:

                pyFace.simulating(tolerance)

            if step >= 6:

                pyFace.reflexing(tolerance)

            if step >= 7:

                pyFace.reviewing(face, tolerance)

            if step >= 8:

                pyFace.rearing(tolerance)

            if step >= 9:

                pyFace.ordinaries(tolerance)

            if step >= 10:

                pyFace.between(tolerance)

            if step >= 11:

                pyFace.aligning(face, tolerance)

            if step >= 12:

                pyFace.ending(tolerance)

        self.Pyth = pyFaceList

        slopeList, planeList, secondaries = [], [], []
        for pyFace in pyFaceList:
            originList = []
            pyWireList = pyFace.wires
            for pyWire in pyWireList:
                numWire = pyWire.numWire
                for pyPlane in pyWire.planes:
                    numAngle = pyPlane.numGeom
                    angle = pyPlane.angle
                    # print '(numAngle, angle) ', (numAngle, angle)
                    if [numWire, numAngle] not in originList:

                        if isinstance(angle, float):
                            # print 'a'
                            slopeList.append(angle)

                            plane = pyPlane.shape
                            if isinstance(plane, list):
                                # print 'aa'
                                planeList.extend(plane[0])
                                secondaries.extend(plane[1:])
                            else:
                                # print 'bb'
                                planeList.append(plane)

                        else:
                            # print 'b'
                            alfa, beta = angle[0], angle[1]

                            if [alfa, beta] not in originList:
                                # print 'bb'
                                originList.append([alfa, beta])

                                if alfa == numWire:
                                    # print 'bb0'

                                    if beta > numAngle:
                                        # print 'bb1'
                                        angle =\
                                            pyWireList[alfa].planes[beta].angle
                                        slopeList.append(angle)

                                        pyPl = pyFace.selectPlane(alfa, beta)
                                        pl = pyPl.shape
                                        planeList.append(pl)

                                elif alfa > numWire:
                                    # print 'bb2'
                                    angle =\
                                        pyWireList[alfa].planes[beta].angle
                                    slopeList.append(angle)

                                    pyPl = pyFace.selectPlane(alfa, beta)
                                    pl = pyPl.shape
                                    planeList.append(pl)

                                elif alfa < numWire:
                                    # print 'bb3'
                                    pass

        planeList.extend(secondaries)
        slopedPlanes.Slopes = slopeList

        for plane in planeList:
            plane.rotate(FreeCAD.Vector(0, 0, 0), sketchAxis,
                         math.degrees(sketchAngle))
            plane.translate(sketchBase)
        endShape = Part.makeShell(planeList)

        if slopedPlanes.Solid:
            if len(faceList) == 1:
                face = faceList[0]
                face.rotate(FreeCAD.Vector(0, 0, 0), sketchAxis,
                            math.degrees(sketchAngle))
                face.translate(sketchBase)
                planeList.extend(faceList)
                endShape = Part.makeShell(planeList)
                endShape = Part.makeSolid(endShape)
            else:
                slopedPlanes.Solid = False

        elif slopedPlanes.Complement:
            endShape.complement()

        # endShape.removeInternalWires(True)
        slopedPlanes.Shape = endShape

    def onChanged(self, slopedPlanes, prop):

        ''''''

        if self.State:
            return

        if prop == 'Slopes':

            slopeList = slopedPlanes.Slopes
            # print 'Slopes slopeList ', slopeList
            if not slopeList:
                return

            numSlope = -1
            pyFaceList = self.Pyth
            for pyFace in pyFaceList:
                originList = []

                pyWireList = pyFace.wires
                for pyWire in pyWireList:
                    numWire = pyWire.numWire
                    # print '### numWire ', numWire

                    numAngle = -1
                    pyPlaneList = pyWire.planes
                    # print[pyPlane.angle for pyPlane in pyPlaneList]
                    for pyPlane in pyPlaneList:
                        numAngle += 1
                        # print '### numAngle ', numAngle
                        angle = pyPlane.angle

                        if [numWire, numAngle] not in originList:

                            if isinstance(angle, float):
                                numSlope += 1
                                # print 'a'
                                pyPlane.angle = slopeList[numSlope]

                            else:
                                # print 'b'
                                alfa, beta = angle[0], angle[1]
                                if [alfa, beta] not in originList:
                                    # print 'c'
                                    originList.append([alfa, beta])

                                    if alfa == numWire:
                                        # print 'd'

                                        if beta > numAngle:
                                            numSlope += 1
                                            # print 'd1'
                                            pyPl =\
                                                pyWireList[alfa].planes[beta]
                                            pyPl.angle = slopeList[numSlope]

                                    elif alfa > numWire:
                                        # print 'e'
                                        numSlope += 1
                                        pyPl =\
                                            pyWireList[alfa].planes[beta]
                                        pyPl.angle = slopeList[numSlope]

                                    elif alfa < numWire:
                                        # print 'f'
                                        pass

                    # print[pyPlane.angle for pyPlane in pyWire.planes]

        elif prop == "SlopeGlobal":

            slope = slopedPlanes.SlopeGlobal
            value = slope
            prop = "angle"
            self.overWritePyProp(prop, value)

        elif prop == "FactorLength":

            length = slopedPlanes.FactorLength
            value = length
            prop = "length"
            self.overWritePyProp(prop, value)

        elif prop == "FactorWidth":

            width = slopedPlanes.FactorWidth
            value = (width, width)
            prop = "width"
            self.overWritePyProp(prop, value)

    def overWritePyProp(self, prop, value):

        ''''''

        for pyFace in self.Pyth:
            for pyWire in pyFace.wires:
                for pyPlane in pyWire.planes:
                    setattr(pyPlane, prop, value)

    def showSimulation(self, slopedPlanes):

        '''firstly recompute'''

        pyFaceList = self.Pyth

        for pyFace in pyFaceList:

            pyAlignList = pyFace.alignaments

            for pyAlign in pyAlignList:
                simul = pyAlign.simulatedShape
                sim = Part.makeCompound(simul)
                Part.show(sim)

    def __getstate__(self):

        ''''''

        state = dict()

        state['Type'] = self.Type

        pyth = []
        for pyFace in self.Pyth:
            dct = pyFace.__dict__.copy()
            wires, alignaments = pyFace.__getstate__()
            dct['_wires'], dct['_alignaments'] = wires, alignaments
            pyth.append(dct)
        state['Pyth'] = pyth

        return state

    def __setstate__(self, state):

        ''''''

        self.Type = state['Type']

        pyth = []
        numFace = -1
        for dct in state['Pyth']:
            numFace += 1
            pyFace = SlopedPlanesPyFace._Face(numFace)
            wires, alignaments = dct['_wires'], dct['_alignaments']
            wires, alignaments = pyFace.__setstate__(wires, alignaments)
            dct['_wires'], dct['_alignaments'] = wires, alignaments
            pyFace.__dict__ = dct
            pyth.append(pyFace)
        self.Pyth = pyth

        self.State = True


class _ViewProvider_SlopedPlanes():

    ''''''

    def __init__(self, vobj):

        ''''''

        vobj.Proxy = self

    def getDefaultDisplayMode(self):

        ''''''

        return "FlatLines"

    def __getstate__(self):

        ''''''

        return None

    def __setstate__(self, state):

        ''''''

        return None

    def attach(self, vobj):

        ''''''

        self.Object = vobj.Object

        obj = self.Object
        obj.Proxy.State = False

    def claimChildren(self):

        ''''''

        obj = self.Object
        base = obj.Base
        return [base]

    def unsetEdit(self, vobj, mode):

        ''''''

        FreeCADGui.Control.closeDialog()
        return

    def setEdit(self, vobj, mode=0):

        ''''''

        taskd = SlopedPlanesTaskPanel._TaskPanel_SlopedPlanes()
        taskd.obj = self.Object
        taskd.update()
        FreeCADGui.Control.showDialog(taskd)
        return True
