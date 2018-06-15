import numpy as np

def field2signal(vectorField):
    ''' a function that reads the inverse of characterization matrix of Sajad's coils '''
    np.set_printoptions(suppress=True)
    fileName = 'InvActMatElements_new.txt'
    rawData = np.loadtxt(fileName)
    invMatrix = np.reshape(rawData,(8,8))
    signal = np.dot(invMatrix.transpose(),vectorField)/1000
    return signal



class FieldManager(object):
    def __init__(self,dac):
        self.vecField = [0,0,0,0,0,0,0,0]
        self.dac = dac

    # Uniform field
    def setField(self,vecField):
        signal = field2signal(vecField)
        self.vecField = vecField
        indexAmplifiers = np.matrix('2; 5; 4; 1; 3; 0; 6; 7')
        for i in range(8):
            self.dac.s826_aoPin(indexAmplifiers.item(i), signal[i])

    def clearField(self):
        self.setField([0,0,0,0,0,0,0,0])
