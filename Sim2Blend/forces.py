

import bpy
from mathutils import Vector
import numpy as np


import os
rootpath=os.path.dirname(os.path.abspath(__file__))
arrowFile=os.path.join(rootpath,'Geometry','arrow.stl')
    


def addForce(collection,bodyName='',position=(0,0,0),rotation=(0,0,0),text="MARKER"):        
    #Add a marker to 3d space    
    # Constants
    DIAMETER=500/1000          
    #Add arrow    
    empty = bpy.data.objects.new(bodyName,None)
    collection.objects.link(empty)
    for obj in bpy.data.objects:
            obj.select_set(False)
    bpy.ops.import_mesh.stl(filepath=arrowFile)
    selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
    obj=selected_objects[0]
    obj.scale=(1,DIAMETER,DIAMETER)
    obj.parent=empty
    obj.users_collection[0].objects.unlink(obj)
    collection.objects.link(obj)                            
                
def fpdata2locrot(data):
    ''' Convert the data from forceplates in the regular format p,v,m to 
    loc and rotxyz
    '''    
    fpNames=readNames(data.dtype.names[1:])    
    headerNames=data.dtype.names[1:]
    
    d=data.view(float,np.ndarray).reshape(data.shape[0],len(headerNames)+1)
    
    N=len(fpNames)
    locidx=np.array([4,5,6]).astype(int)
    
    for i in range(N):
        locidx=np.concatenate([locidx,N*9+locidx])
                
    #Use data to determine the locrot of this thing and then make a matrix
    #with that info.   
    baselocidx=np.array([4,5,6])
    locidx=[]
    for i in range(0,N):
        locidx=np.concatenate((locidx,i*9+baselocidx))

    idx=locidx.astype(int)

    tails=d[:,idx]  
    arrow=d[:,idx-3]  
    rotvals=np.copy(tails)
    scalevals=np.copy(tails)
    
    originalarrow=Vector([1,0,0])    
    for i in range(0,arrow.shape[0]):
        for j in range(0,N):
            #Generate rotation XYZ based on arrow and origin vector
            thisarrow=Vector([arrow[i,j*3],arrow[i,j*3+1],arrow[i,j*3+2]])   
            normarrow=thisarrow.normalized()             
            quat=originalarrow.rotation_difference(normarrow)
            eul=quat.to_euler('XYZ') #maybe use compatibility arg
            rotvals[i,3*j] = eul[0]*180/np.pi
            rotvals[i,3*j+1] = eul[1]*180/np.pi
            rotvals[i,3*j+2] = eul[2]*180/np.pi
            #Genarate scale in x based on magnitude of arrow
            scalevals[i,j*3]=thisarrow.magnitude/700
            if (thisarrow.magnitude<20):
                scalevals[i,j*3+1]=0
                scalevals[i,j*3+2]=0
            else:
                scalevals[i,j*3+1]=1
                scalevals[i,j*3+2]=1
            
            if (j==3):
                print(fpNames[j])
                print(thisarrow)
                print(normarrow)
                print(eul)
                  
    alltbl=np.zeros((tails.shape[0],tails.shape[1]*3))

    locidx=[]
    rotidx=[]
    scaleidx=[]
    baselocidx=np.array([0,1,2])
    for i in range(0,N):
        locidx=np.concatenate((locidx,i*9+baselocidx))
        rotidx=np.concatenate((rotidx,i*9+3+baselocidx))
        scaleidx=np.concatenate((scaleidx,i*9+6+baselocidx))

    alltbl[:,locidx.astype(int)]=tails
    alltbl[:,rotidx.astype(int)]=rotvals
    alltbl[:,scaleidx.astype(int)]=scalevals
            
    header=np.expand_dims(data['Header'],1)
    alltbl=np.concatenate([header,alltbl],axis=1)
    colnames=['Header']    
    
    for i in range(0,N):
        thisfpcols=[fpNames[i]+'_x',fpNames[i]+'_y',fpNames[i]+'_z',
               fpNames[i]+'_rotx',fpNames[i]+'_roty',fpNames[i]+'_rotz',
               fpNames[i]+'_scalex',fpNames[i]+'_scaley',fpNames[i]+'_scalez'] 
        colnames=colnames+thisfpcols
        
    out=np.core.records.fromarrays(alltbl.transpose(),names=colnames)
    
    return out
    
def import_forces(csvFileName):    
    '''
    Load forces by reading a csv file containing the frame index and the p v (and optional m) values.
    '''
    data = np.genfromtxt(csvFileName, dtype=float, delimiter=',', names=True,skip_header=0) 
    fpNames=readNames(data.dtype.names[1:])    
    headerNames=data.dtype.names[1:]    
    N=len(fpNames)

    #'''
    ####Create Arrows for each fpname
    newCol = bpy.data.collections.new('forces')
    bpy.context.scene.collection.children.link(newCol)
    for forceName in fpNames:        
        addForce(newCol,bodyName=forceName,text=forceName)
    a=bpy.data.collections['forces']
    #'''
    d=fpdata2locrot(data)
    loadAnimation(a,d,fpNames)
    

    

''' 
#Example
fileName='G:\\Dropbox (GaTech)\\PvA\\TestScaling\\test.csv' 
loadMarkers(fileName)
'''