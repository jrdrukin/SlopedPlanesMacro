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


import FreeCAD
import Part
import SlopedPlanesUtils as utils
import SlopedPlanesPy
import SlopedPlanesPyWire
import SlopedPlanesPyReflex
import SlopedPlanesPyAlignament
import SlopedPlanesPyPlane


__title__ = "SlopedPlanes Macro"
__author__ = "Damian Caceres Moreno"
__url__ = "http://www.freecadweb.org"


class _Face(SlopedPlanesPy._Py):

    ''''''

    def __init__(self, numFace):

        ''''''

        self.numFace = numFace
        self.wires = []
        self.alignaments = []
        self.reset = False

    @property
    def numFace(self):

        ''''''

        return self._numFace

    @numFace.setter
    def numFace(self, numFace):

        ''''''

        self._numFace = numFace

    @property
    def wires(self):

        ''''''

        return self._wires

    @wires.setter
    def wires(self, wires):

        ''''''

        self._wires = wires

    @property
    def alignaments(self):

        ''''''

        return self._alignaments

    @alignaments.setter
    def alignaments(self, alignaments):

        ''''''

        self._alignaments = alignaments

    @property
    def reset(self):

        ''''''

        return self._reset

    @reset.setter
    def reset(self, reset):

        ''''''

        self._reset = reset

    def __getstate__(self):

        ''''''

        wireList = []
        for wire in self.wires:
            dct = wire.__dict__.copy()
            dct['_coordinates'] = [[v.x, v.y, v.z] for v in wire.coordinates]
            dct['_shapeGeom'] = []

            planeList = []
            for plane in wire.planes:
                dd = plane.__dict__.copy()
                dd['_shape'], dd['_bigShape'], dd['_enormousShape'],\
                    dd['_geom'], dd['_geomAligned'],\
                    dd['_cutter'], dd['_oppCutter'],\
                    dd['_forward'], dd['_backward'] =\
                    None, None, None, None, None, [], [], None, None
                planeList.append(dd)
            dct['_planes'] = planeList

            reflexList = []
            for reflex in wire.reflexs:
                dd = reflex.__dict__.copy()
                planes = [[plane.numWire, plane.numGeom]
                          for plane in reflex.planes]
                dd['_planes'] = planes
                reflexList.append(dd)
            dct['_reflexs'] = reflexList

            wireList.append(dct)

        alignList = []
        for align in self.alignaments:
            dct = align.__dict__.copy()
            dct['_aligns'] = [[plane.numWire, plane.numGeom]
                              for plane in align.aligns]
            dct['_chops'] = [[[plane.numWire, plane.numGeom],
                             [pl.numWire, pl.numGeom]] for [plane, pl]
                             in align.chops]
            base = align.base
            dct['_base'] = [base.numWire, base.numGeom]
            dct['_simulatedShape'] = None
            alignList.append(dct)

        return wireList, alignList

    def __setstate__(self, wires, alignaments):

        ''''''

        wireList = []
        numWire = -1
        for dct in wires:
            numWire += 1
            wire = SlopedPlanesPyWire._Wire(numWire)

            planeList = []
            numGeom = -1
            for dd in dct['_planes']:
                numGeom += 1
                plane = SlopedPlanesPyPlane._Plane(numWire, numGeom)
                plane.__dict__ = dd
                planeList.append(plane)
            dct['_planes'] = planeList

            reflexList = []
            for dd in dct['_reflexs']:
                reflex = SlopedPlanesPyReflex._Reflex()
                for [numWire, numGeom] in dd['_planes']:
                    plane = planeList[numGeom]
                    reflex.addLink('planes', plane)
                dd['_planes'] = reflex.planes
                reflex.__dict__ = dd
                reflexList.append(reflex)
            dct['_reflexs'] = reflexList

            coord = dct['_coordinates']
            coordinates = [FreeCAD.Vector(v) for v in coord]
            dct['_coordinates'] = coordinates

            wire.__dict__ = dct
            wireList.append(wire)

        alignList = []
        for dct in alignaments:
            alignament = SlopedPlanesPyAlignament._Alignament()
            for [numWire, numGeom] in dct['_aligns']:
                plane = wireList[numWire].planes[numGeom]
                alignament.addLink('aligns', plane)
            dct['_aligns'] = alignament.aligns

            for [[numWire, numGeom], [nWire, nGeom]] in dct['_chops']:
                plane = wireList[numWire].planes[numGeom]
                pl = wireList[nWire].planes[nGeom]
                alignament.addLink('chops', [plane, pl])
            dct['_chops'] = alignament.chops

            [numWire, numGeom] = dct['_base']
            base = wireList[numWire].planes[numGeom]
            dct['_base'] = base

            alignament.__dict__ = dct
            alignList.append(alignament)

        return wireList, alignList

    def parsing(self, normal, size, tolerance):

        ''''''

        print '######### parsing'

        pyWireList = self.wires

        resetFace = self.reset
        if resetFace:
            for pyWire in pyWireList:
                pyWire.reflexs = []

        self.alignaments = []

        shapeGeomFace = []
        for pyWire in pyWireList:
            shapeGeomFace.extend(pyWire.shapeGeom)

        for pyWire in pyWireList:
            numWire = pyWire.numWire
            print '###### numWire ', numWire
            ref = False

            lenWire = len(pyWire.planes)
            coord = pyWire.coordinates
            eje = coord[1].sub(coord[0])
            pyPlaneList = pyWire.planes
            for pyPlane in pyPlaneList:
                numGeom = pyPlane.numGeom
                print '### numGeom ', numGeom
                geom = pyPlane.geom

                if ref:
                    print 'ref'

                    # OJO
                    if pyPlane.geomAligned:
                        line = pyPlane.geom

                        lineStartParam = line.FirstParameter
                        lineEndParam = lineStartParam - size

                        forwardLine =\
                            Part.LineSegment(line, lineStartParam,
                                             lineEndParam)
                        # print 'forwardLine ', forwardLine
                        forwardLineShape = forwardLine.toShape()

                        lineStartParam = line.LastParameter
                        lineEndParam = lineStartParam + size

                        backwardLine =\
                            Part.LineSegment(line, lineStartParam,
                                             lineEndParam)
                        # print 'backwardLine ', backwardLine
                        backwardLineShape = backwardLine.toShape()

                        pyPlane.backward = backwardLineShape
                        pyPlane.forward = forwardLineShape

                    ref = False

                    if resetFace:
                        # OJO
                        if pyPlane.geomAligned:
                            print 'ref 1'
                            self.seatReflex(pyWire, pyReflex, pyPlane,
                                            'backward', tolerance)

                    print 'rear ', pyPlane.rear

                nextEje = coord[numGeom+2].sub(coord[numGeom+1])
                corner = utils.convexReflex(eje, nextEje, normal, numWire)
                print 'corner ', corner
                eje = nextEje

                line = geom

                lineLastParam = line.LastParameter
                lineEndParam = lineLastParam + size
                forwardLine = Part.LineSegment(line, lineLastParam,
                                               lineEndParam)
                # print 'forwardLine ', forwardLine
                lineEnd = coord[numGeom+1]
                forwardLineShape = forwardLine.toShape()

                lineStartParam = line.FirstParameter
                lineEndParam = lineStartParam - size

                backwardLine =\
                    Part.LineSegment(line, lineStartParam, lineEndParam)
                # print 'backwardLine ', backwardLine
                backwardLineShape = backwardLine.toShape()

                if ((numWire == 0 and corner == 'reflex') or
                   (numWire > 0 and corner == 'convex')):
                    print '1'

                    section = forwardLineShape.section(shapeGeomFace,
                                                       tolerance)

                    if section.Edges:
                        print '11'

                        numEdge = -1
                        for edge in section.Edges:
                            numEdge += 1
                            print '111'
                            edgeStart = edge.firstVertex(True).Point
                            point = utils.roundVector(edgeStart, tolerance)
                            (nWire, nGeom) =\
                                self.findAlignament(point, tolerance)

                            pyW = pyWireList[nWire]
                            pyPl = pyW.planes[nGeom]

                            if pyPl.geomAligned:
                                print '111a'

                                edgeEnd = edge.lastVertex(True).Point
                                distStart = edgeStart.sub(lineEnd).Length
                                distEnd = edgeEnd.sub(lineEnd).Length

                                if distStart < distEnd:
                                    print '1111'

                                    if numEdge == 0:
                                        pyAlign =\
                                            SlopedPlanesPyAlignament._Alignament()
                                        self.addLink('alignaments', pyAlign)
                                        pyAlign.base = pyPlane

                                    fAng = self.findAngle(numWire, numGeom)
                                    sAng = self.findAngle(nWire, nGeom)

                                    if fAng == sAng:
                                        print '11111'

                                        fGeom = pyPlane.geomAligned
                                        sGeom = pyPl.geomAligned
                                        pyPl.geomAligned = None
                                        pyPl.angle = [numWire, numGeom]

                                        eStartParam = fGeom.FirstParameter
                                        eEndPoint = sGeom.EndPoint
                                        eEndParam =\
                                            forwardLine.parameter(eEndPoint)
                                        eGeom =\
                                            Part.LineSegment(fGeom,
                                                             eStartParam,
                                                             eEndParam)
                                        pyPlane.geomAligned = eGeom

                                        self.seatAlignament(pyAlign,
                                                            pyWire, pyPlane,
                                                            pyW, pyPl,
                                                            shapeGeomFace,
                                                            size, tolerance)

                                        if pyPl.numWire == pyPlane.numWire:
                                            ref = True

                                        pyReflex =\
                                            SlopedPlanesPyReflex._Reflex()

                                    else:
                                        print '11112'
                                        # falseAlignament

                                else:
                                    print '1112'
                                    # no alignament
                                    # pyReflex
                                    # rear
                                    # ref = True
                                    # break

                            else:
                                print '111b'
                                if pyPl.numWire == pyPlane.numWire:
                                    ref = True
                                # OJO
                                pyReflex = SlopedPlanesPyReflex._Reflex()

                        else:
                            # OJO
                            if corner == 'reflex':
                                if resetFace:
                                    print 'end'
                                    line = pyPl.geom
                                    lineLastParam = line.LastParameter
                                    lineEndParam = lineLastParam + size
                                    forwardLine =\
                                        Part.LineSegment(line, lineLastParam,
                                                         lineEndParam)
                                    # print 'forwardLine ', forwardLine
                                    forwardLineShape = forwardLine.toShape()
                                    pyPlane.forward = forwardLineShape

                                    self.seatReflex(pyWire, pyReflex, pyPlane,
                                                    'forward', tolerance)

                    else:
                        print '12'

                        if corner == 'reflex':

                            pyPlane.forward = forwardLineShape
                            pyPlane.backward = backwardLineShape
                            ref = True

                            if resetFace:
                                print '121'
                                pyReflex = SlopedPlanesPyReflex._Reflex()
                                pyWire.addLink('reflexs', pyReflex)
                                self.seatReflex(pyWire, pyReflex, pyPlane,
                                                'forward', tolerance)

                else:
                    print '2'
                    if corner == 'reflex':
                        if not pyPlane.choped:
                            num = utils.sliceIndex(numGeom+1, lenWire)
                            pyNextPlane = pyPlaneList[num]
                            if not pyNextPlane.choped:

                                pyPlane.forward = forwardLineShape
                                pyPlane.backward = backwardLineShape
                                ref = True

                                if resetFace:
                                    print '21'
                                    pyReflex = SlopedPlanesPyReflex._Reflex()
                                    pyWire.addLink('reflexs', pyReflex)
                                    self.seatReflex(pyWire, pyReflex, pyPlane,
                                                    'forward', tolerance)

                print 'rear ', pyPlane.rear

            pyWire.reset = False

        print '********* wires ', self.wires
        for pyWire in self.wires:
            print '****** numWire ', pyWire.numWire
            print '*** print reflexs ', pyWire.reflexs
            for pyReflex in pyWire.reflexs:
                print 'rangoInter ', pyReflex.rangoInter
                print 'planes ', pyReflex.planes
                for pyPlane in pyReflex.planes:
                    print pyPlane.numGeom,\
                        pyPlane.rear,\
                        pyPlane.rango

        print '********* alignaments ', self.alignaments
        for pyAlignament in self.alignaments:
            print '****** base'
            print 'numWire ', pyAlignament.base.numWire
            print 'numGeom ', pyAlignament.base.numGeom
            print 'rear ', pyAlignament.base.rear
            print 'rango ',  pyAlignament.base.rango
            print 'rangoChop ', pyAlignament.rangoChop

            print '*** chops ', [[(x.numWire, x.numGeom),
                                  (y.numWire, y.numGeom)]
                                 for [x, y] in pyAlignament.chops]
            for chop in pyAlignament.chops:
                for pyPlane in chop:
                    print(pyPlane.numWire, pyPlane.numGeom), ' ',\
                        pyPlane.rear,\
                        pyPlane.rango

            print '*** aligns ', [x.numGeom for x in pyAlignament.aligns]
            for align in pyAlignament.aligns:
                print(align.numWire, align.numGeom),\
                    align.rear,\
                    align.rango

    def seatAlignament(self, pyAlign, pyWire, pyPlane, pyW, pyPl,
                       shapeGeomFace, size, tolerance):

        ''''''

        print '# seatAlignament'

        numWire = pyWire.numWire
        numGeom = pyPlane.numGeom
        print 'pyPlane.numWire ', pyPlane.numWire
        print 'pyPlane.numGeom ', pyPlane.numGeom
        pyPlane.reflexed = True
        pyPlane.aligned = True

        nWire = pyW.numWire
        nGeom = pyPl.numGeom
        print 'pyPl.numWire ', pyPl.numWire
        print 'pyPl.numGeom ', pyPl.numGeom
        pyPl.reflexed = True
        pyPl.aligned = True
        pyPl.shape = None
        # OJO
        # if not pyPl.choped:
        pyPl.rear = []

        if pyPl.reflexed:
            self.removeReflex(pyW, pyPl)

        aL = pyAlign.aligns

        lenWire = len(pyWire.planes)
        if aL:
            num = aL[-1].numGeom
            chopOne = utils.sliceIndex(num+1, lenWire)
            numC = aL[-1].numWire
        else:
            chopOne = utils.sliceIndex(numGeom+1, lenWire)
            numC = numWire

        aL.append(pyPl)

        pyAli = self.selectAlignament(nWire, nGeom)
        if pyAli:
            bL = pyAli.aligns
            aL.extend(bL)
            for b in bL:
                b.angle = [numWire, numGeom]

        pyWireList = self.wires

        if numWire == nWire:
            print 'a'
            chopTwo = utils.sliceIndex(nGeom-1, lenWire)
        else:
            print 'b'
            lenW = len(pyWireList[nWire].planes)
            chopTwo = utils.sliceIndex(nGeom-1, lenW)

        print 'chopOne ', (numC, chopOne)
        print 'chopTwo ', (nWire, chopTwo)

        cL = pyAlign.chops
        pyOne = self.selectPlane(numC, chopOne)
        pyOne.reflexed = True
        pyOne.choped = True
        pyTwo = self.selectPlane(nWire, chopTwo)
        pyTwo.reflexed = True
        pyTwo.choped = True
        cL.append([pyOne, pyTwo])

        if pyAli:
            dL = pyAli.chops
            cL.extend(dL)

        pyAlign.aligns = aL
        pyAlign.chops = cL

        if pyAli:
            self.removeAlignament(pyAli)

    def seatReflex(self, pyWire, pyReflex, pyPlane, direction, tolerance):

        ''''''

        print '# seatReflex'

        pyReflex.addLink('planes', pyPlane)
        pyPlane.reflexed = True

        shapeGeomWire = pyWire.shapeGeom
        numWire = pyWire.numWire
        lenWire = len(pyWire.planes)
        numGeom = pyPlane.numGeom
        lineShape = pyPlane.forward
        section = lineShape.section(shapeGeomWire, tolerance)

        print[v.Point for v in section.Vertexes]
        print section.Edges
        print lenWire
        print len(section.Vertexes)
        print direction

        if section.Edges:
            print 'a'
            if direction == 'forward':
                print 'aa'
                vertex = section.Edges[0].Vertexes[0]
            else:
                print 'aaa'
                vertex = section.Edges[-1].Vertexes[1]

        elif len(section.Vertexes) != lenWire:
            print 'b'
            vertex = section.Vertexes[1]

        else:
            print 'c'
            # uhfs
            if pyPlane.aligned:
                print 'cc'
                if pyPlane.shape:
                    lineEndPoint = pyPlane.geomAligned.EndPoint
                    if section.Vertexes[0].Point == lineEndPoint:
                        return
                    else:
                        vertex = section.Vertexes[1]
                else:
                    return
            else:
                print 'ccc'
                vertex = section.Vertexes[1]

        print vertex.Point

        # if not pyPlane.aligned:

        nGeom =\
            self.findRear(pyWire, pyPlane, vertex, direction, tolerance)

        if direction == 'forward':
            endNum = utils.sliceIndex(numGeom+2, lenWire)
        else:
            endNum = utils.sliceIndex(numGeom-2, lenWire)

        print 'direction, endNum ', direction, endNum

        if nGeom == endNum:
            pyPl = self.selectPlane(numWire, endNum)
            print 'arrow'
            pyPl.arrow = True

        if pyPlane.choped:
            reflexs = pyWire.reflexs
            try:
                reflexs.remove(pyReflex)
                pyWire.reflexs = reflexs
            except ValueError:
                pass

    def findRear(self, pyWire, pyPlane, vertex, direction, tolerance):

        ''''''

        print 'findRear'

        shapeGeomWire = pyWire.shapeGeom
        lenWire = len(pyWire.planes)
        section = vertex.section(shapeGeomWire, tolerance)
        if len(section.Vertexes) > lenWire:
            print 'a'
            nGeom = -1
            for shape in shapeGeomWire:
                nGeom += 1
                sect = vertex.section([shape], tolerance)
                if len(sect.Vertexes) > 0:
                    break
        else:
            print 'b'
            coord = pyWire.coordinates
            nGeom = coord.index(vertex.Point)
            if direction == 'forward':
                nGeom = utils.sliceIndex(nGeom-1, lenWire)

        pyPlane.addValue('rear', nGeom, direction)

        return nGeom

    def findAngle(self, nW, nG):

        ''''''

        pyWireList = self.wires

        pyW = pyWireList[nW]
        pyPl = pyW.planes[nG]
        angle = pyPl.angle

        if isinstance(angle, list):
            angle = self.findAngle(angle[0], angle[1])

        return angle

    def findAlignament(self, point, tolerance):

        ''''''

        for pyWire in self.wires:
            nWire = pyWire.numWire
            coordinates = pyWire.coordinates
            try:
                nGeom = coordinates.index(point)
                break
            except ValueError:
                pass

        return (nWire, nGeom)

    def selectAlignament(self, nWire, nGeom):

        ''''''

        pyAlignList = self.alignaments
        for align in pyAlignList:
            if align.base.numWire == nWire:
                if align.base.numGeom == nGeom:
                    return align

        return None

    def selectReflex(self, numWire, numGeom, nGeom):

        ''''''

        pyReflexList = self.wires[numWire].reflexs
        for pyReflex in pyReflexList:
            [pyPlane, pyPl] = pyReflex.planes
            [nn, mm] = [pyPlane.numGeom, pyPl.numGeom]
            if [nn, mm] == [numGeom, nGeom] or [nn, mm] == [nGeom, numGeom]:
                return pyReflex

        return None

    def selectAllReflex(self, numWire, numGeom):

        ''''''

        pyRList = []
        pyReflexList = self.wires[numWire].reflexs
        for pyReflex in pyReflexList:
            [pyPlane, pyPl] = pyReflex.planes
            [nn, mm] = [pyPlane.numGeom, pyPl.numGeom]
            if numGeom in [nn, mm]:
                pyRList.append(pyReflex)

        return pyRList

    def selectPlane(self, nWire, nGeom):

        ''''''

        pyWireList = self.wires
        for wire in pyWireList:
            if wire.numWire == nWire:
                pyPlaneList = wire.planes
                for plane in pyPlaneList:
                    if plane.numGeom == nGeom:
                        return plane

        return None

    def removeReflex(self, pyWire, pyPlane):

        ''''''

        pyReflexList = pyWire.reflexs
        for reflex in pyReflexList:
            if pyPlane in reflex.planes:
                pyReflexList.remove(reflex)
        pyWire.reflexs = pyReflexList

    def removeAlignament(self, pyAlign):

        ''''''

        pyAlignList = self.alignaments
        pyAlignList.remove(pyAlign)
        self.alignaments = pyAlignList

    def planning(self, normal, size, reverse):

        ''''''

        print '######### planning'

        pyWireList = self.wires
        reset = self.reset

        for pyWire in pyWireList:

            pyWire.planningWire(reset, normal, size, reverse)

        print '###### alignament rangos'

        pyAlignList = self.alignaments

        for pyAlign in pyAlignList:
            if reset:

                pyAlign.ranggingAlign(self)

            pyAlign.ranggingChop(self)

        self.reset = False

    def trimming(self, tolerance):

        ''''''

        print '######### trimming'

        for pyWire in self.wires:
            pyWire.trimmingWire(self, tolerance)

        for pyAlign in self.alignaments:
            pyAlign.trimmingAlign(self, tolerance)

    def priorLater(self, tolerance):

        ''''''

        print '######### priorLater'

        for pyWire in self.wires:

            pyWire.priorLaterWire(self, tolerance)

    def simulating(self, tolerance):

        ''''''

        print '######### simulating'

        pyAlignList = self.alignaments

        for pyAlign in pyAlignList:
            pyAlign.simulateAlignament(self, tolerance)

    def reflexing(self, tolerance):

        ''''''

        print '######### reflexing'

        for pyWire in self.wires:

            if pyWire.reflexs:

                for pyReflex in pyWire.reflexs:
                    pyReflex.processReflex(self, pyWire, tolerance)

                for pyReflex in pyWire.reflexs:
                    pyReflex.solveReflex(tolerance)

    def reviewing(self, face, tolerance):

        ''''''

        print '######### reviewing'

        for pyWire in self.wires:
            if len(pyWire.reflexs) > 1:

                pyWire.reviewWire(tolerance)

                solved, unsolved = pyWire.clasifyReflexPlanes(tolerance)
                print[p.numGeom for p in solved]
                print[p.numGeom for p in unsolved]

                pyWire.reProcessReflexs(tolerance, solved, unsolved)

                pyWire.betweenReflexs(tolerance)

    def rearing(self, tolerance):

        ''''''

        print '######### rearing'

        for pyWire in self.wires:

            if pyWire.reflexs:

                for pyReflex in pyWire.reflexs:
                    for pyPlane in pyReflex.planes:
                        pyPlane.solveRear(pyWire, pyReflex, tolerance)

    def ordinaries(self, tolerance):

        ''''''

        print '######### ordinaries'

        for pyWire in self.wires:
            for pyPlane in pyWire.planes:
                # if not (pyPlane.choped and not pyPlane.aligned):
                if not (pyPlane.reflexed and not pyPlane.aligned):
                    if pyPlane.shape:
                        # print '###### (numWire, numGeom) ',\
                            # (pyPlane.numWire, pyPlane.numGeom)
                        pyPlane.solvePlane(self, pyWire, tolerance)

    def between(self, tolerance):

        ''''''

        pyWireList = self.wires
        if len(pyWireList) > 1:

            print '######### between'

            numWire = -1
            for pyWire in pyWireList:
                numWire += 1
                # print 'numWire ', numWire
                pop = pyWireList.pop(numWire)
                cutterList = []
                for pyW in pyWireList:
                    pyPlaneList = pyW.planes
                    # nW = pyW.numWire
                    for pyPl in pyPlaneList:
                        if not pyPl.choped:
                            if not pyPl.aligned:
                                pl = pyPl.shape
                                cutterList.append(pl)
                pyWireList.insert(numWire, pop)

                for pyPlane in pyWire.planes:
                    # print 'numGeom ', pyPlane.numGeom
                    plane = pyPlane.shape
                    if plane:
                        if cutterList:
                            gS = pyPlane.geomAligned.toShape()
                            plane = plane.cut(cutterList, tolerance)
                            plane = utils.selectFace(plane.Faces, gS,
                                                     tolerance)
                            pyPlane.shape = plane

    def aligning(self, face, tolerance):

        ''''''

        print '######### aligning'

        pyAlignList = self.alignaments

        for pyAlign in pyAlignList:
            pyAlign.solveAlignament(face, self, tolerance)

    def ending(self, tolerance):

        ''''''

        print '######### ending'

        pyAlignList = self.alignaments

        cutterList = []

        for pyAlign in pyAlignList:

            base = pyAlign.base.shape
            if base not in cutterList:
                cutterList.append(base)
                # print 'a', pyAlign.base.numGeom

            for pyPlane in pyAlign.aligns:
                plane = pyPlane.shape
                if plane:
                    if plane not in cutterList:
                        cutterList.append(plane)
                        # print 'b', pyPlane.numGeom

            for [pyChopOne, pyChopTwo] in pyAlign.chops:
                chopOne = pyChopOne.shape

                if chopOne:
                    if chopOne not in cutterList:
                        cutterList.append(chopOne)
                        # print 'c', pyChopOne.numGeom
                chopTwo = pyChopTwo.shape

                if chopTwo:
                    if chopTwo not in cutterList:
                        cutterList.append(chopTwo)
                        # print 'd', pyChopTwo.numGeom

        # print 'cutterList ', cutterList

        if cutterList:

            for pyWire in self.wires:
                for pyPlane in pyWire.planes:
                    # if not (pyPlane.aligned or pyPlane.choped):
                    # if not pyPlane.aligned:
                    plane = pyPlane.shape
                    if plane:

                        # print '~~~~~~~~~ (numWire, numGeom) ',\
                            # (pyPlane.numWire, pyPlane.numGeom)

                        if pyPlane.choped or pyPlane.aligned:
                            # print 'aa'
                            cutterList.remove(plane)

                        plane = plane.cut(cutterList, tolerance)
                        gS = pyPlane.geom.toShape()
                        plane = utils.selectFace(plane.Faces, gS, tolerance)
                        pyPlane.shape = plane

                        if pyPlane.choped or pyPlane.aligned:
                            # print 'bb'
                            cutterList.append(plane)
