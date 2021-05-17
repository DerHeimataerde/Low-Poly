import os
import numpy
import sys
import bpy
import glob
import traceback
import subprocess
from progress.bar import Bar
import contextlib
import fileinput

def replaceAll(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

if len(sys.argv) > 1:
    root_dir = sys.argv[1]
    decimateratio = float(sys.argv[2])
    if len(sys.argv) > 3:
        eng_path = sys.argv[3]
        if not (os.path.exists(eng_path)):
            print("studiomdl.exe path not resolvable. Search for \\Left 4 Dead 2\\bin\\studiomdl.exe")
    else:
        eng_path = "C:\\Program Files (x86)\\Steam\\SteamApps\\common\\Left 4 Dead 2\\bin\\studiomdl.exe"
    game_path = eng_path[0:-17]+"left4dead2"

else:
    print("..Usage:")
    print("     lp.py \'\\path\\to\\models\\directory\\to\\decimate\' decimate-ratio-as-float \'\\path\\to\\studiomdl.exe\\\'")
    print("..Decimation ratio MUST be from 0 to 1 as a float")
    print("..If studiomdl.exe path is omitted, defaults to standard C drive install dir")
    print("..Final compiled models are found in \\left4dead2\\models")
    quit()

if (root_dir[-1] != "\\"):
    root_dir = root_dir+"\\"

verbose = False
if ("-v" in sys.argv):
    verbose = True
    
bstpath = os.path.dirname(os.path.realpath(__file__))+"\\blender_source_tools_3.1.0.zip"

#Decompiling files
filecount=0
countedfiles= []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    if (filename.endswith('.mdl') and (not (filename in countedfiles)) and (not ('anim' in filename)) and (not ('break' in filename))):
        filecount += 1
        countedfiles.append(filename)
bar = Bar('Decompiling', max=(filecount))
print()

editedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    try:
        if (os.path.isfile(filename) and (not (filename in editedfiles))):
            if (filename.endswith('.mdl') and (not ('anim' in filename)) and (not ('break' in filename))):
                filepath = "\\".join(filename.split("\\")[0:-1])
                print("DECOMPILING: "+filename)
                args = ["CrowbarCommandLineDecomp.exe", "-p", filename, "-o", filepath]
                if verbose:
                    subprocess.run(args)
                else:
                    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                editedfiles.append(filename)
                print()
                bar.next()
                print()
    except:
        print(str(filename)+": ERROR")
        traceback.print_exc()
        input("Press Enter to continue...")
        continue
bar.finish()

'''
#Removing extra/previous files.
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    try:
        if os.path.isfile(filename):
            if not (filename.endswith('.smd') or filename.endswith('.qc') or filename.endswith('.vta')):
                print("DELETING: "+filename)
                os.remove(filename)
    except:
        print(str(filename)+": ERROR")
        traceback.print_exc()
        input("Press Enter to continue...")
        continue
'''
#Decimating models using blender python module

filecount=0
countedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    if (filename.endswith('.smd') and (not (filename in countedfiles)) and (not ('phys' in filename)) and (not filename.endswith('idle.smd')) and (not ('anim' in filename))):
        filecount += 1
        countedfiles.append(filename)
bar = Bar('Decimating', max=(filecount))
print()

editedfiles = []

for filename in glob.iglob(root_dir + '**/**', recursive=True):
    try:
        if (os.path.isfile(filename) and (not (filename in editedfiles))):
            if (filename.endswith('.smd') and (not filename.endswith('physics.smd')) and (not filename.endswith('idle.smd'))
             and (not ('anim' in filename)) and (not ('_OLD' in filename))):
                print("DECIMATING: "+filename)

                old_target = sys.stdout
                old_err = sys.stderr
                if not verbose:
                    sys.stdout = open(os.devnull, 'w')
                    sys.stderr = open(os.devnull, 'w')

                filedir = os.path.dirname(filename)
                bpy.ops.wm.read_factory_settings()
                bpy.ops.preferences.addon_install(filepath=bstpath)
                bpy.ops.preferences.addon_enable(module='io_scene_valvesource')
                bpy.ops.wm.save_userpref()

                for c in bpy.context.scene.collection.children:
                    bpy.context.scene.collection.children.unlink(c)
                for c in bpy.data.objects:
                    bpy.data.objects.remove(c)

                bpy.ops.import_scene.smd(filepath=filename)
                os.rename(filename,filename[0:-4]+"_OLD.smd")
                for obj in bpy.context.scene.objects:
                    print(obj)
                for obj in bpy.context.scene.objects:
                    if not obj.name.endswith('skeleton'):
                        bpy.context.view_layer.objects.active = obj
                        
                        modifier = obj.modifiers.new(name='Decimate', type='DECIMATE')
                        modifier.ratio = decimateratio
                        '''
                        #for mod in obj.modifiers:
                            #bpy.ops.object.modifier_apply(modifier=mod.name)
                            #bpy.ops.object.modifier_apply(modifier='DECIMATE')
                        '''

                bpy.context.scene.vs.export_format = 'SMD'
                bpy.context.scene.vs.export_path = filedir
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.export_scene.smd()
                editedfiles.append(filename)
                #print("EDITED FILES: "+str(editedfiles))

                sys.stdout = old_target
                sys.stderr = old_err
                print()
                bar.next()
                print()
    except:
        print(str(filename)+": ERROR")
        traceback.print_exc()
        input("Press Enter to continue...")
        continue
bar.finish()
'''
#Removing hand kinematics (fixes hand animations)
filecount=0
countedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    if (filename.endswith('.qc') and (not (filename in countedfiles))):
        filecount += 1 
        countedfiles.append(filename)
bar = Bar('Reconfiguring', max=(filecount))
print()

editedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    try:
        if os.path.isfile(filename):
            if (filename.endswith('.qc') and (not (filename in editedfiles))):
                print("Reconfiguring: "+filename)
                replaceAll(filename,"ikrule","//ikrule")
                editedfiles.append(filename)
                print()
                bar.next()
                print()

    except:
        traceback.print_exc()
        input("Press Enter to continue...")
        continue
bar.finish()
'''

input("Press Enter to Compile")
#Compiling models

filecount=0
countedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    if (filename.endswith('.qc') and (not (filename in countedfiles))):
        filecount += 1 
        countedfiles.append(filename)
bar = Bar('Compiling', max=(filecount))
print()

editedfiles = []
for filename in glob.iglob(root_dir + '**/**', recursive=True):
    try:
        if os.path.isfile(filename):
            if (filename.endswith('.qc') and (not (filename in editedfiles))):
                print("COMPILING: "+filename)
                args = [eng_path, "-game", game_path, "-nop4", "-verbose", "-nox360", filename]
                if verbose:
                    subprocess.run(args)
                else:
                    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                editedfiles.append(filename)
                print()
                bar.next()
                print()

    except:
        traceback.print_exc()
        input("Press Enter to continue...")
        continue
bar.finish()
print("Finished processing.")