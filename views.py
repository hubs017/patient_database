from django.shortcuts import render
from django.http import HttpResponse
from django.core.files import File
from django.core.files.base import ContentFile
from .models import Patient, Bed, Personel
import json
import abc
import hashlib
import time

class PatientDatabaseRequestHandler():
    __metaclass__ = abc.ABCMeta
    def __init__(self, request, session):
        self.request = request
        self.session = session

    @abc.abstractmethod
    def print_response(self):
        "Returns response in Http format"
        pass

class PDHelloWorldRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        return HttpResponse("Hello world!")
    
class PDGetByPeselRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        patient = Patient.objects.get(pesel = self.request["pesel"])
        return HttpResponse(patient.serialize())        

class PDGetByBedIdRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        bed_identifier = self.request["bed_id"]
        bed = self.get_bed_from_bed_identifier(bed_identifier)
        if (bed.patient != None):
            return HttpResponse(bed.patient.serialize())
        else:
            return HttpResponse("False")

    def get_bed_from_bed_identifier(self, bed_identifier):
        bed_id = bed_identifier.split("-")
        bed_id_num = [int(x) for x in bed_id]
        return Bed.objects.get(floor=bed_id_num[0], room=bed_id_num[1], bed_number=bed_id_num[2])

class PDInsertPatientRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        patient = Patient(name = self.request["patient_name"],
                        surname = self.request["patient_surname"],
                        age = self.request["patient_age"],
                        birth_date = self.request["birth_date"],
                        pesel = self.request["pesel"])
        patient.save()
        return HttpResponse("True")

class PDAssignPatientRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        if (self.assign_bed()):
            return HttpResponse("True")    
        else:
            return HttpResponse("False")

    def assign_bed(self):
        bed = self.get_bed_from_bed_identifier(self.request["bed_id"])
        if (bed.patient == None):
            patient = Patient.objects.get(pesel = self.request["pesel"])
            bed.patient = patient
            bed.save()
            return True
        else:
            if (self.request["pesel"] == "none"):
                bed.patient = None
                bed.save()
                return True
            else:
                return False

    def get_bed_from_bed_identifier(self, bed_identifier):
        bed_id = bed_identifier.split("-")
        bed_id_num = [int(x) for x in bed_id]
        return Bed.objects.get(floor=bed_id_num[0], room=bed_id_num[1], bed_number=bed_id_num[2])

class PDUpdateRecommendationRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        patient = Patient.objects.get(pesel = self.request["pesel"])
        if(patient != None):
            patient.doctor_recommendations = self.request["recommendation"]
            patient.save()
            return HttpResponse("True")
        else:
            return HttpResponse("False")

class PDGetAllBedsRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        return HttpResponse(self.serialize_all_beds())

    def serialize_all_beds(self):
        serializable_beds = []
        for bed in Bed.objects.all():
            serializable_beds.append(bed)

        return json.dumps(serializable_beds, default=Bed.serialize)

class PDLogInRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        if (self.validate_user()):
            self.session["logged_in"] = True
            return HttpResponse(self.user.serialize())
        else:
            return HttpResponse("False")

    def validate_user(self):
        user_name = self.request.get("user")
        if (user_name == None):
            return False
        user_name = user_name.split(".")
        name = user_name[0]
        surname = user_name[1]
        password = self.request.get("password")
        hashed_pass = hashlib.sha512(password.encode())

        user = Personel.objects.get(name = name, surname = surname)
        if (user.password == hashed_pass.hexdigest()):
            self.user = user
            return True
        else:
            return False

class PDLogOutRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        self.session["logged_in"] = False
        return HttpResponse("True")

class PDNotLoggedInRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        return HttpResponse("You should log in first")

class PDUpdatePatientTemperatureRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        patient = Patient.objects.get(pesel = self.request.get("pesel"))
        temp_file = patient.temp_measurments
        date = time.strftime("%d/%m/%Y %H:%M", time.localtime())
        if (temp_file == None):
            file_name = patient.name + "_" + patient.surname + "_temp.csv"
            temp_file.save(file_name, ContentFile(date + ", " + self.request.get("temp") + "\n"))
        else:
            temp_file.open("a")
            temp_file.write(date + ", " + self.request.get("temp") + "\n")
            temp_file.close()

        return HttpResponse("True")

class PDGetTempMeasurmentsRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        patient = Patient.objects.get(pesel = self.request.get("pesel"))
        temp_file = patient.temp_measurments
        if (temp_file == None):
            return HttpResponse("False")
        else:
            temp_file.open(mode = "r")
            measurments = temp_file.read()
            temp_file.close()
            return HttpResponse(measurments)

class PDInvalidOperationRequestHandler(PatientDatabaseRequestHandler):
    def print_response(self):
        return HttpResponse("Invalid operation")



class PatientDatabaseRequestHandlerFactory:
    def __init__(self, request, session):
        self.session = session
        self.request = request
        action = request.get("action")
        self.response = PDInvalidOperationRequestHandler(request, session)
        if (action != "login" and (not self.authenticate_user())):
            self.response = PDNotLoggedInRequestHandler(request, session)
        else:
            if (action == "login"):
                self.response = PDLogInRequestHandler(request, session)
            elif (action == "logout"):
                self.response = PDLogOutRequestHandler(request, session)
            elif (action == None):
                self.response = PDHelloWorldRequestHandler(request, session)
            elif(action == "get_by_bed"):
                self.response = PDGetByBedIdRequestHandler(request, session)
            elif(action == "get_by_pesel"):
                self.response = PDGetByPeselRequestHandler(request, session)
            elif(action == "insert"):
                self.response = PDInsertPatientRequestHandler(request, session)
            elif(action == "assign"):
                self.response = PDAssignPatientRequestHandler(request, session)
            elif(action == "update_recommendation"):
                self.response = PDUpdateRecommendationRequestHandler(request, session)
            elif(action == "get_all_beds"):
                self.response = PDGetAllBedsRequestHandler(request, session)
            elif(action == "update_temp"):
                self.response = PDUpdatePatientTemperatureRequestHandler(request, session)
            elif(action == "get_temp_measurments"):
                self.response = PDGetTempMeasurmentsRequestHandler(request, session)

    def get_handler(self):
        return self.response

    def authenticate_user(self):
        logged_in = self.session.get("logged_in")
        if(logged_in == None or logged_in == False):
            token = self.request.get("token")
            if (token == None):
                return False
            else:
                return self.validate_token(token)
        else:
            return True

    #@TODO: validate the token passed in the request
    def validate_token(self, token):
        return True


def index(request):
    if (request.method == 'GET'):
        response = PatientDatabaseRequestHandlerFactory(request.GET, request.session).get_handler()
    elif (request.method == 'POST'):
        response = PatientDatabaseRequestHandlerFactory(request.POST, request.session).get_handler()
    return response.print_response()
