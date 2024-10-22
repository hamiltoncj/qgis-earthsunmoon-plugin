"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .sunposition_limited import SunPositionAlgorithm
from .daynight import DayNightAlgorithm

class EarthSunMoonProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(SunPositionAlgorithm())
        self.addAlgorithm(DayNightAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/sun.svg')

    def id(self):
        return 'earthsunmoon'

    def name(self):
        return 'Earth, sun, moon & planets'

    def longName(self):
        return self.name()
