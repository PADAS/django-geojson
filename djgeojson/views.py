import math

from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
#from django.contrib.gis.geos.geometry import Polygon

from .http import HttpJSONResponse
from .serializers import Serializer as GeoJSONSerializer
from . import GEOJSON_DEFAULT_SRID


class GeoJSONResponseMixin(object):
    """
    A mixin that can be used to render a GeoJSON response.
    """
    response_class = HttpJSONResponse
    """ Select fields for properties """
    properties = []
    """ Limit float precision """
    precision = None
    """ Simplify geometries """
    simplify = None
    """ Change projection of geometries """
    srid = GEOJSON_DEFAULT_SRID
    """ Geometry field to serialize """
    geometry_field = 'geom'
    """ Force 2D """
    force2d = False
    """ bbox """
    bbox = None
    """ bbox auto """
    bbox_auto = False

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        serializer = GeoJSONSerializer()
        response = self.response_class(**response_kwargs)
        options = dict(properties=self.properties,
                       precision=self.precision,
                       simplify=self.simplify,
                       srid=self.srid,
                       geometry_field=self.geometry_field,
                       force2d=self.force2d,
                       bbox=self.bbox,
                       bbox_auto=self.bbox_auto)
        serializer.serialize(self.get_queryset(), stream=response, ensure_ascii=False,
                             **options)
        return response


class GeoJSONLayerView(GeoJSONResponseMixin, ListView):
    """
    A generic view to serve a model as a layer.
    """
    @method_decorator(gzip_page)
    def dispatch(self, *args, **kwargs):
        return super(GeoJSONLayerView, self).dispatch(*args, **kwargs)


class TiledGeoJSONLayerView(GeoJSONLayerView):
    width = 256
    height = 256
    tile_srid = 3857
    trim_to_boundary = True

    def tile_coord(self, xtile, ytile, zoom):
        """
        This returns the NW-corner of the square. Use the function 
        with xtile+1 and/or ytile+1 to get the other corners.
        With xtile+0.5 & ytile+0.5 it will return the center of the tile.
        http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._2
        """
        assert self.tile_srid == 3857, 'Custom tile projection not supported yet'
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)

    # def __call__(self, request, z, x, y):
    #     """
    #     Glen Roberton's django-geojson-tiles view
    #     """
    #     z = int(z)
    #     x = int(x)
    #     y = int(y)

    #     bbox = self.coords_to_bbox_mmap(z, x, y)

    #     shapes = self.get_queryset().filter(**{
    #         '%s__intersects' % self.geometry_field: bbox
    #     })
    #     model_field = shapes.model._meta.get_field(self.geometry_field)
    #     # Can't trim point geometries to a boundary
    #     self.trim_to_boundary = (self.trim_to_boundary and
    #                              not isinstance(model_field, PointField))

    #     if self.trim_to_boundary:
    #         shapes = shapes.intersection(bbox)
    #         self.geometry_field = 'intersection'
