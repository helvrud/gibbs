import bpy, math
import numpy as np
#~ import pickle
import _pickle as cPickle
import sys
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()
sys.path.append('.')
#~ import gel
sys.path.append('/home/kvint/hydrogel/espresso/es-build/src/python')
#import espressomd

def makeMaterial(name, diffuse, specular, alpha):

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat

def setMaterial(ob, mat):

    me = ob.data
    me.materials.append(mat)



materials = {'red': makeMaterial('Red',(1,0,0),(0,0,0),1),
             'green': makeMaterial('Blue',(0,1,0),(0,0,0),1),
             'blue': makeMaterial('Blue',(0,0,1),(0,0,0),1),
             'grey': makeMaterial('Grey',(0.25,0.25,0.25),(0,0,0),1),
             'white': makeMaterial('White',(1.,1.,1.),(0,0,0),1),
             'black': makeMaterial('Black',(0.,0.,0.),(0,0,0),1)}

def sphere(name='', xyz=[0,0,0], color='red', radius=1.0):
    #~ global a 
    bpy.ops.mesh.primitive_uv_sphere_add(size=radius,location=xyz)
    bpy.ops.object.shade_smooth()
    #~ bpy.ops.mesh.primitive_cone_add(vertices=4, radius=1, depth=1, cap_end=True, view_align=False, enter_editmode=False, location=origin, rotation=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.show_name = False
    me = ob.data
    me.name = name+'Mesh'
    setMaterial(ob, materials[color])
    return ob

def bond(o0, o1, radius = 0.1):
    #Location of target objects
    x0 = o0.location.x;
    y0 = o0.location.y;
    z0 = o0.location.z;
    x1 = o1.location.x;
    y1 = o1.location.y;
    z1 = o1.location.z;
    #Center between the two objects.
    xc = x0 + ((x1-x0)/2);
    yc = y0 + ((y1-y0)/2);
    zc = z0 + ((z1-z0)/2);
    #Position of o1 if an imaginary sphere encompassing
    #both objects was transformed to 0, 0, 0
    xt = x1-xc;
    yt = y1-yc;
    zt = z1-zc;
    #--------------------------------------------
    #Spherical coordinates (radius r, inclination theta, azimuth phi) from 
    #the Cartesian coordinates (x, y, z) of o1 on our imaginary sphere
    r = math.sqrt( (xt*xt) + (yt*yt) + (zt*zt) );
    try: theta = math.acos( zt/r );
    except ZeroDivisionError: theta = 0
    phi = math.atan2( (yt), (xt) );
    #--------------------------------------------
    #Add a cylinder that is the length of our imaginary sphere
    #and is rotated to point in the direction of object 1.
    bpy.ops.mesh.primitive_cylinder_add(
        location = (xc, yc, zc),
        depth = r*2,
        radius = radius,
        rotation = (0, theta, phi)
    );
    #--------------------------------------------
    #Name the cylinder
    bpy.context.active_object.name = 'connect' + '_' + o0.name + '_' + o1.name;
    
def box(box_l=1):
    b = box_l
    radius = 0.1
    s1 = sphere(radius = radius,xyz = (0,0,0), color = 'grey', name = 'v1' )
    s2 = sphere(radius = radius,xyz = (b,0,0), color = 'grey', name = 'v2' )
    s3 = sphere(radius = radius,xyz = (0,b,0), color = 'grey', name = 'v3' )
    s4 = sphere(radius = radius,xyz = (b,b,0), color = 'grey', name = 'v4' )
    s5 = sphere(radius = radius,xyz = (0,0,b), color = 'grey', name = 'v5' )
    s6 = sphere(radius = radius,xyz = (0,b,b), color = 'grey', name = 'v6' )
    s7 = sphere(radius = radius,xyz = (b,b,b), color = 'grey', name = 'v7' )
    s8 = sphere(radius = radius,xyz = (b,0,b), color = 'grey', name = 'v8' )
    bond(s1, s2, radius = radius)
    bond(s1, s3, radius = radius)
    bond(s1, s5, radius = radius)
    bond(s3, s6, radius = radius)
    bond(s3, s4, radius = radius)
    bond(s6, s7, radius = radius)
    bond(s6, s5, radius = radius)
    bond(s7, s8, radius = radius)
    bond(s7, s4, radius = radius)
    bond(s8, s2, radius = radius)
    bond(s8, s5, radius = radius)
    bond(s4, s2, radius = radius)

def plot(pkl_file, plot_bonds = True):
    global box_l
    print(pkl_file)
    #~ from .gel import gel
    pkl_file = open(pkl_file, 'rb')
    load = cPickle.load(pkl_file)
    pkl_file.close()
    coords = load['part']['pos']
    coords = coords % load['box_l'] # this wraps coordinates to box_l
    bonds = load['part']['bonds']
    types = load['part']['type']
    ids = load['part']['id']
    box_l = load['box_l']
    names = load['NAMES']
    #~ print (bonds)
    #~ coords = 10*np.random.random([10,3])
    spheres = []
    i = 0
    #~ spheres.append(name = str(ids[i]), sphere(radius = 0.1,xyz = coords[0]))
    for i in range(len(coords)):
        color = 'red'
        radius = 0.2
        if types[i] == 0: color = 'green'
        elif types[i] == 1: color = 'red'
        elif types[i] == 2: color = 'red'; radius = 0.1
        elif types[i] == 3: color = 'green'; radius = 0.1
        elif types[i] == 4: color = 'red'; radius = 0.1
        elif types[i] == 5: color = 'grey'; radius = 0.1
        elif types[i] == 6: color = 'grey'; radius = 0.1
        elif types[i] == 7: color = 'blue'; radius = 0.1
        elif types[i] == 8: color = 'grey'; radius = 0.1
        elif types[i] == 9: color = 'blue'; radius = 0.1
        elif types[i] == 10: color = 'white'; radius = 0.2
        else: color = 'black'
        spheres.append(sphere(name = str(names[types[i]])+str(ids[i]), radius = radius, xyz = coords[i], color = color))
        #~ print (s)
    if plot_bonds:
        for i in range(len(bonds)):
            s0 = spheres[bonds[i][0]]
            for b in bonds[i]:
                
                s1 = spheres[b]
                l = s0.location - s1.location
                if (np.linalg.norm(l) < box_l/2.) and (np.linalg.norm(l)>0):
                    bond(s0, s1)
    box(box_l = box_l)
    

print('#######')
#pkl_file =  sys.argv[3]
pkl_file =  'data/gel_pCl4.00_box_l70.pkl_dict'

#~ print('#######')
print(pkl_file)

#~ pkl_file = '/home/kvint/hydrogel/data/acid_N10_M1_box_l10.pkl'
#~ pkl_file = '/home/kvint/hydrogel/data/acid_N10_M1_box_l10.pkl'
#~ print( pkl_file )
#~ print ('###########')
#~ print (pkl_file)
plot(pkl_file, plot_bonds = True)
#~ for x in linspace(0,10):



pi = np.pi
tx = 0.0
ty = 0.0
tz = 80.0

rx = 0.0
ry = 0.0
rz = 0.0

fov = 50.0

scene = bpy.data.scenes["Scene"]

# Set render resolution
#~ scene.render.resolution_x = 480
#~ scene.render.resolution_y = 359

# Set camera fov in degrees
scene.camera.data.angle = fov*(pi/180.0)

# Set camera rotation in euler angles
scene.camera.rotation_mode = 'XYZ'
scene.camera.rotation_euler[0] = rx*(pi/180.0)
scene.camera.rotation_euler[1] = ry*(pi/180.0)
scene.camera.rotation_euler[2] = rz*(pi/180.0)

# Set camera translation
scene.camera.location.x = 0
scene.camera.location.y = -box_l
scene.camera.location.z = -box_l

scene.camera.rotation_euler[0] = 3*pi/4
scene.camera.rotation_euler[1] = pi/4
scene.camera.rotation_euler[2] = 0
