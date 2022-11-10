from flask import Flask, jsonify, request, redirect, send_from_directory
import face_recognition
import requests
import numpy
from firebase import firebase
from PIL import Image
from io import BytesIO
#Firebase Setup
firebase = firebase.FirebaseApplication('https://smartsafe-b8132.firebaseio.com/', None)

#Flask Setup
app = Flask(__name__)

#Dummy Faces Dictionary
Faces = {
          'id':1,
          'name': "Obama",
          'Embeddings': [ ]
         }

status = {
           'status': None,
           'id': None
         }

@app.route('/rest/api/faces/Authenticate', methods=['GET'])
def Authenticate():

    FaceDetected = False
    while FaceDetected == False:
        image = CapturePhoto()
        FaceDetected = DetectFace(image)
        print("Cara Detectada:" + str(FaceDetected))

    UserName, AuthStatus, UserID = Authenticate(image)

    print(AuthStatus)
    #Abre la caja fuerte, notifica webApp usuario logeado y estado de autenticacion
    if AuthStatus == True:
            status['status'] = AuthStatus
            status['id'] = UserID
            requests.get('http://10.0.0.18:5001/rest/api/safe/Open')
            print("se envio senal de Open a Raspberry")
            return jsonify(status)

    else:
        status['status'] = AuthStatus
        status['id'] = None
        return jsonify(status)


@app.route('/rest/api/faces/AddUser', methods=['GET'])
def AddUser():
    #Argumento se ponen http://localhost:5002/rest/api/faces/AddUser?id=?&name?
    UserID = request.args.get('id')
    UserName = request.args.get('name')

    Faces['name'] = UserName
    Faces['id'] = UserID
    firebase.post('https://smartsafe-b8132.firebaseio.com/users', Faces)

    status['status'] = True
    status['id'] = UserID

    return jsonify(status)


@app.route('/rest/api/faces/AddFace', methods=['GET'])
def AddFace():
    #Argumento se ponen http://localhost:5002/rest/api/faces/AddFace?id=?&name=?
    #consigue nombre de usuario con el ID, FireBaseID
    UserID = request.args.get('id')

    FireBaseKey, UserName = GetUserInfo(UserID)

    if FireBaseKey == "none":
        return "User ID not found"

    FaceDetected = False
    while FaceDetected == False:
        image = CapturePhoto()
        FaceDetected = DetectFace(image)
    #esta funcion registra la cara de la persona en la base de datos
    AuthStatus = AddEmbedding(image, FireBaseKey)
    status['status'] = AuthStatus
    status['id'] = UserID

    return jsonify(status)

def CapturePhoto():

    r = requests.get('http://10.0.0.18:5001/rest/api/safe/Capture')

    #falta agregar condicional para que no explote
    i = BytesIO(r.content)

    print("Conversion de Imagen a Bytes")

    return i


def GetUserInfo(UserID):
    #Verfica si el ID del usuario existe o no si lo comprueba retorna el nombre del usuario y su FireBaseID
    List = []
    UserName = "dummy"
    FireBaseKey = 0
    id = UserID
    for j in firebase.get('https://smartsafe-b8132.firebaseio.com/users',''):
        j = str(j)
        List.append(j)

    for i in range(len(List)):
        FBKey = firebase.get('https://smartsafe-b8132.firebaseio.com/users/{}/id'.format(List[i]),'')
        if  str(FBKey) == str(id):
            UserName = firebase.get('https://smartsafe-b8132.firebaseio.com/users/{}/name'.format(List[i]),'')
            FireBaseKey = List[i]
            break


    if UserName == "dummy":
        return "none", "none"
    else:
        return FireBaseKey, UserName


def DetectFace(file):
    image = face_recognition.load_image_file(file)

    #Returna un array con el cuadro de la seccion de la foto donde esta la cara
    FaceBox = face_recognition.face_locations(image)

    if len(FaceBox) > 0:
        return True
    else:
        return False


def Authenticate(file):

    #Carga Imagen
    image = face_recognition.load_image_file(file)

    #Returna un array con el cuadro de la seccion de la foto donde esta la cara
    FaceBox = face_recognition.face_locations(image)

    #Calcula los encodings
    FaceEncd = face_recognition.face_encodings(image, FaceBox)
    print("Calcule los encondings")

    UserName = "None"
    AuthStatus = False
    UserID = None
    Faces = firebase.get('https://smartsafe-b8132.firebaseio.com/users','')

    for x in Faces:
        Face = firebase.get('https://smartsafe-b8132.firebaseio.com/users/{}'.format(x),'')
        #if len(Faces) == 3:
        result = face_recognition.compare_faces(Face['Embeddings'], FaceEncd[0], tolerance=0.4)
        print(len(Face['Embeddings']))
        print(Face['name'])
        print(result)
        for i in range(len(result)):

            if result[i] == True:
                print("Valide la condicion")
                AuthStatus = True
                UserName = str(Face['name'])
                UserID = str(Face['id'])
                FaceEncd = FaceEncd[0].tolist()
                Face['Embeddings'].append(FaceEncd)
                firebase.delete('https://smartsafe-b8132.firebaseio.com/users/', x)
                firebase.post('https://smartsafe-b8132.firebaseio.com/users',Face)
                print("subi la cara de " + str(UserName))
                break
        if AuthStatus == True:
            break



    return (UserName, AuthStatus, UserID)

def AddEmbedding(image, FireBaseKey):

    file = face_recognition.load_image_file(image)

    #Returna un array con el cuadro de la seccion de la foto donde esta la cara
    FaceBox = face_recognition.face_locations(file)

    #Calcula los encodings
    FaceEncd = face_recognition.face_encodings(file, FaceBox)
    FaceEncd = FaceEncd[0].tolist()

    Faces = firebase.get('https://smartsafe-b8132.firebaseio.com/users/{}'.format(FireBaseKey),'')
    if len(Faces) != 3:
        Faces['Embeddings'] = []
    Faces['Embeddings'].append(FaceEncd)
    firebase.delete('https://smartsafe-b8132.firebaseio.com/users/',FireBaseKey)
    firebase.post('https://smartsafe-b8132.firebaseio.com/users',Faces)

    return True

def RegisterEmbedding(image, UserName, UserID):
    file = face_recognition.load_image_file(image)

    #Returna un array con el cuadro de la seccion de la foto donde esta la cara
    FaceBox = face_recognition.face_locations(file)

    #Calcula los encodings
    FaceEncd = face_recognition.face_encodings(file, FaceBox)
    FaceEncd = FaceEncd[0].tolist()
    Faces['Embeddings'].append(FaceEncd)
    Faces['name'] = UserName
    Faces['id'] = UserID
    firebase.post('https://smartsafe-b8132.firebaseio.com/users', Faces)

    return True

app.run(host='10.0.0.40', port=5002)
