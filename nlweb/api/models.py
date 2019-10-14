from django.db import models

# Create your models here.

from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point

SRID = 4326

class HasLocation(models.Model):
    class Meta:
        abstract=True

    location = PointField(null=True)

    def set_location(self, longitude, latitude):
        self.location = Point(longitude, latitude, srid=SRID)

    @property
    def latitude(self):
        if self.location is None:
            return None
        return self.location.y

    @property
    def longitude(self):
        if self.location is None:
            return None
        return self.location.x

# q: define "CruiseGroup"?

class Cruise(models.Model):
    name = models.CharField(max_length=64, unique=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

class Cast(HasLocation):
    cruise = models.ForeignKey('Cruise', related_name='casts', on_delete=models.CASCADE)
    number = models.IntegerField(null=True)
    # designation is for when the cast doesn't have a number or has an additional text id
    designation = models.CharField(max_length=64)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    max_depth = models.FloatField(null=True)
    
class Niskin(HasLocation):
    cast = models.ForeignKey('Cast', related_name='niskins', on_delete=models.CASCADE)
    target_depth = models.FloatField(null=True)
    target_depth_designation = models.CharField(max_length=64) # e.g., 'chl max'
    time = models.DateTimeField()
    depth = models.FloatField()

class Sample(models.Model):
    sample_id = models.CharField(max_length=64, null=True)
    volume = models.FloatField(null=True)
    niskins = models.ManyToManyField('Niskin')
    # attribution

class Station(HasLocation):
    cruise = models.ForeignKey('Cruise', related_name='stations', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)

# need person (PI) model
# need keywords for stuff like parameters
# need file descriptions of variables including data type
# model for term from a vocabulary
# instrument types
