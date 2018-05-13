from django.test import TestCase
from .models import Patient
from .views import *
import json
from datetime import date

# Create your tests here.

def patient_database_set_up():
    Patient.objects.create(name = "John",
                            surname = "Smith",
                            age = 20,
                            birth_date = date(year=1994, month=1, day=25),
                            pesel = "90012509019")

class PatientModelTestCase(TestCase):
    def setUp(self):
        patient_database_set_up()

    def test_serialization(self):
        patient = Patient.objects.get(id=1)
        serialized_patient = patient.serialize()
        patient_dict = json.loads(serialized_patient)
        self.assertEqual(patient_dict["name"], "John")
        self.assertEqual(patient_dict["surname"], "Smith")
        self.assertEqual(patient_dict["age"], 20)
        self.assertEqual(patient_dict["birth_date"], "1994-01-25")
        self.assertEqual(patient_dict["pesel"], "90012509019")

