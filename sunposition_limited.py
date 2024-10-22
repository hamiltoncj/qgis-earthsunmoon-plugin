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
from datetime import timedelta
from .terminator import Terminator

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsField, QgsFields, QgsVectorLayer,
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsSvgMarkerSymbolLayer)

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDefinition,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink)

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from .utils import epsg4326, settings, SolarObj, parse_timeseries

class SunPositionAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to display the sun directly overhead.
    """

    PrmOutputLayer = 'OutputLayer'
    PrmDateTime = 'DateTime'
    PrmTimeSeries = 'TimeSeries'
    PrmTimeIncrement = 'TimeIncrement'
    PrmTimeDuration = 'TimeDuration'
    PrmStyle = 'Style'

    def initAlgorithm(self, config):

        dt = QDateTime.currentDateTime()
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.PrmDateTime,
                'Select date and time for calculations',
                type=QgsProcessingParameterDateTime.DateTime,
                defaultValue=dt,
                optional=False,
                )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmStyle,
                'Automatically style output',
                True,
                optional=False)
        )
        # Time Series Support
        param = QgsProcessingParameterBoolean(
                self.PrmTimeSeries,
                'Create sun time series',
                False,
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        param = QgsProcessingParameterString(
                self.PrmTimeIncrement,
                'Time increment between observations (DD:HH:MM:SS)',
                defaultValue='00:01:00:00',
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterString(
                self.PrmTimeDuration,
                'Total duration for sun positions (DD:HH:MM:SS)',
                defaultValue='1:00:00:00',
                optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Sun Position')
        )

    def processAlgorithm(self, parameters, context, feedback):
        auto_style = self.parameterAsBool(parameters, self.PrmStyle, context)
        qdt = self.parameterAsDateTime(parameters, self.PrmDateTime, context)
        generate_timeseries = self.parameterAsBool(parameters, self.PrmTimeSeries, context)
        time_increment = self.parameterAsString(parameters, self.PrmTimeIncrement, context)
        time_duration = self.parameterAsString(parameters, self.PrmTimeDuration, context)
        if generate_timeseries:
            num_events, time_delta = parse_timeseries(time_increment, time_duration)
        else:
            num_events = 1
            time_delta = 0
        if num_events == -1:
            raise QgsProcessingException('Invalid time increment and/or duration.')

        f = QgsFields()
        f.append(QgsField("object_id", QVariant.Int))
        f.append(QgsField("name", QVariant.String))
        f.append(QgsField("latitude", QVariant.Double))
        f.append(QgsField("longitude", QVariant.Double))
        f.append(QgsField("timestamp", QVariant.Double))
        f.append(QgsField("datetime", QVariant.String))
        f.append(QgsField("utc", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, f,
            QgsWkbTypes.Point, epsg4326)

        qutc = qdt.toUTC()
        utc = qutc.toPyDateTime()
        for i in range(num_events):
            delta = i*time_delta
            utc_cur = utc + timedelta(seconds=delta)
            lon, lat = Terminator.solar_position(utc_cur)
            
            feat = QgsFeature()
            attr = [SolarObj.SUN.value, 'Sun', float(lat), float(lon), utc_cur.timestamp(), qdt.addSecs(delta).toString('yyyy-MM-dd hh:mm:ss'), qutc.addSecs(delta).toString('yyyy-MM-dd hh:mm:ss')]
            feat.setAttributes(attr)
            pt = QgsPointXY(lon, lat)
            feat.setGeometry(QgsGeometry.fromPointXY(pt))
            sink.addFeature(feat)

        if auto_style and context.willLoadLayerOnCompletion(dest_id):
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(StylePostProcessor.create())

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'sunposition'

    def displayName(self):
        return 'Sun position directly overhead'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/sun.svg')

    '''def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)'''

    def createInstance(self):
        return SunPositionAlgorithm()

class StylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        path = os.path.join(os.path.dirname(__file__), 'icons/sun.svg')
        symbol = QgsSvgMarkerSymbolLayer(path)
        symbol.setSize(10)
        layer.renderer().symbol().changeSymbolLayer(0, symbol )
        layer.triggerRepaint()
            

    @staticmethod
    def create() -> 'StylePostProcessor':
        """
        Returns a new instance of the post processor keeping a reference to the sip
        wrapper so that sip doesn't get confused with the Python subclass and call
        the base wrapper implemenation instead.
        """
        StylePostProcessor.instance = StylePostProcessor()
        return StylePostProcessor.instance
