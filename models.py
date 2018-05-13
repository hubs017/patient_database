from __future__ import unicode_literals

from django.db import models
import json

class Personel(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    password = models.CharField(max_length=200)
    DOCTOR = 'MD'
    NURSE = 'NU'
    NON_MEDICAL_STAFF = 'NM'
    ROLE_CHOICES = ((DOCTOR, 'Doctor'), (NURSE, 'Nurse'), (NON_MEDICAL_STAFF, 'Non medical staff'))
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default=NON_MEDICAL_STAFF)

    def serialize(self):
        return json.dumps({"role" : self.role,
                            "token" : "magic_token"})

class Patient(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    age = models.IntegerField()
    birth_date = models.DateField()
    pesel = models.CharField(max_length=12, unique = True)
    doctor_recommendations = models.CharField(max_length=2000, null=True)
    temp_measurments = models.FileField(upload_to='temp/', null=True)

    def serialize(self):
        return json.dumps({"name" : self.name,
                            "surname" : self.surname, 
                            "age" : self.age, 
                            "birth_date" : self.birth_date.strftime("%Y-%m-%d"),
                            "pesel" : self.pesel,
                            "recommendations" : self.doctor_recommendations})


class Bed(models.Model):
    floor = models.IntegerField()
    room = models.IntegerField()
    bed_number = models.IntegerField()
    patient = models.OneToOneField(Patient, null=True)

    def serialize(self):
        return json.dumps({"address" : self.get_bed_address(), "occupied" : self.is_occupied()})

    def get_bed_address(self):
        return str(self.floor) + "-" + str(self.room) + "-" + str(self.bed_number)

    def is_occupied(self):
        if (self.patient is None):
            return False
        else:
            return True
