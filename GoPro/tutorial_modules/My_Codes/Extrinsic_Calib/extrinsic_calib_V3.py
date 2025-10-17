import shutil
import datetime
import os
import logging
## INIT
import numpy as np
import pandas as pd
os.environ["OPENCV_LOG_LEVEL"]="FATAL"
import cv2
import glob
import toml
import re
import warnings
import matplotlib.pyplot as plt
from mpl_interactions import zoom_factory, panhandler
from PIL import Image


#import pickle
#from lxml import etree
#from contextlib import contextmanager,redirect_stderr,redirect_stdout
#from os import devnull

#To run this code:

def euclidean_distance(q1, q2):
    '''
    Euclidean distance between 2 points (N-dim).
    
    INPUTS:
    - q1: list of N_dimensional coordinates of point
         or list of N points of N_dimensional coordinates
    - q2: idem

    OUTPUTS:
    - euc_dist: float. Euclidian distance between q1 and q2
    '''
    
    q1 = np.array(q1)
    q2 = np.array(q2)
    dist = q2 - q1
    if np.isnan(dist).all():
        dist = np.empty_like(dist)
        dist[...] = np.inf
    
    if len(dist.shape)==1:
        euc_dist = np.sqrt(np.nansum( [d**2 for d in dist]))
    else:
        euc_dist = np.sqrt(np.nansum( [d**2 for d in dist], axis=1))
    
    return euc_dist

def zup2yup(Q):
    '''
    Turns Z-up system coordinates into Y-up coordinates
    INPUT:
    - Q: pandas dataframe
    N 3D points as columns, ie 3*N columns in Z-up system coordinates
    and frame number as rows
    OUTPUT:
    - Q: pandas dataframe with N 3D points in Y-up system coordinates
    '''

    # X->Y, Y->Z, Z->X
    cols = list(Q.columns)
    cols = np.array([[cols[i*3+1],cols[i*3+2],cols[i*3]] for i in range(int(len(cols)/3))]).flatten()
    Q = Q[cols]

    return Q

def calib_calc_fun(calib_dir, intrinsics_config_dict, extrinsics_config_dict):
    '''
    Calibrates intrinsic and extrinsic parameters
    from images or videos of a checkerboard
    or retrieve them from a file

    INPUTS:
    - calib_dir: directory containing intrinsic and extrinsic folders, each populated with camera directories
    - intrinsics_config_dict: dictionary of intrinsics parameters (overwrite_intrinsics, show_detection_intrinsics, intrinsics_extension, extract_every_N_sec, intrinsics_corners_nb, intrinsics_square_size, intrinsics_marker_size, intrinsics_aruco_dict)
    - extrinsics_config_dict: dictionary of extrinsics parameters (calculate_extrinsics, show_detection_extrinsics, extrinsics_extension, extrinsics_corners_nb, extrinsics_square_size, extrinsics_marker_size, extrinsics_aruco_dict, object_coords_3d)

    OUTPUTS:
    - ret: residual reprojection error in _px_: list of floats
    - C: camera name: list of strings
    - S: image size: list of list of floats
    - D: distorsion: list of arrays of floats
    - K: intrinsic parameters: list of 3x3 arrays of floats
    - R: extrinsic rotation: list of arrays of floats (Rodrigues)
    - T: extrinsic translation: list of arrays of floats
    '''
    overwrite_intrinsics = intrinsics_config_dict.get('overwrite_intrinsics')
    overwrite_intrinsics=False
    calculate_extrinsics = extrinsics_config_dict.get('calculate_extrinsics')

    # retrieve intrinsics if calib_file found and if overwrite_intrinsics=False
    try:
        calib_file = glob.glob(os.path.join(calib_dir, f'Calib*.toml'))[0]
    except:
        pass
    if not overwrite_intrinsics and 'calib_file' in locals():
        logging.info(f'\nPreexisting calibration file found: \'{calib_file}\'.')
        logging.info(f'\nRetrieving intrinsic parameters from file. Set "overwrite_intrinsics" to true in Config.toml to recalculate them.')
        calib_file = glob.glob(os.path.join(calib_dir, f'Calib*.toml'))[0]
        calib_data = toml.load(calib_file)

        ret, C, S, D, K, R, T = [], [], [], [], [], [], []
        for cam in calib_data:
            if cam != 'metadata':
                ret += [0.0]
                C += [calib_data[cam]['name']]
                S += [calib_data[cam]['size']]
                K += [np.array(calib_data[cam]['matrix'])]
                D += [calib_data[cam]['distortions']]
                R += [[0.0, 0.0, 0.0]]
                T += [[0.0, 0.0, 0.0]]
        nb_cams_intrinsics = len(C)
    
    # calculate intrinsics otherwise
    else:
        logging.info(f'\nCalculating intrinsic parameters...')
        ret, C, S, D, K, R, T = calibrate_intrinsics(calib_dir, intrinsics_config_dict)
        nb_cams_intrinsics = len(C)

    # calculate extrinsics
    if calculate_extrinsics:
        logging.info(f'\nCalculating extrinsic parameters...')
        
        # check that the number of cameras is consistent
        nb_cams_extrinsics = len(next(os.walk(os.path.join(calib_dir, 'extrinsics')))[1])
        if nb_cams_intrinsics != nb_cams_extrinsics:
            raise Exception(f'Error: The number of cameras is not consistent:\
                    Found {nb_cams_intrinsics} cameras based on the number of intrinsic folders or on calibration file data,\
                    and {nb_cams_extrinsics} cameras based on the number of extrinsic folders.')
        ret, C, S, D, K, R, T = calibrate_extrinsics(calib_dir, extrinsics_config_dict, C, S, K, D)
    else:
        logging.info(f'\nExtrinsic parameters won\'t be calculated. Set "calculate_extrinsics" to true in Config.toml to calculate them.')

    return ret, C, S, D, K, R, T

def imgp_objp_visualizer_clicker(img, imgp=[], objp=[], img_path=''):
    '''
    Shows image img. 
    If imgp is given, displays them in green
    If objp is given, can be displayed in a 3D plot if 'C' is pressed.
    If img_path is given, just uses it to name the window

    If 'Y' is pressed, closes all and returns confirmed imgp and (if given) objp
    If 'N' is pressed, closes all and returns nothing
    If 'C' is pressed, allows clicking imgp by hand. If objp is given:
        Displays them in 3D as a helper. 
        Left click to add a point, right click to remove the last point.
        Press 'H' to indicate that one of the objp is not visible on image
        Closes all and returns imgp and objp if all points have been clicked
    Allows for zooming and panning with middle click
    
    INPUTS:
    - img: image opened with openCV
    - optional: imgp: detected image points, to be accepted or not. Array of [[2d corner coordinates]]
    - optional: objp: array of [3d corner coordinates]
    - optional: img_path: path to image

    OUTPUTS:
    - imgp_confirmed: image points that have been correctly identified. array of [[2d corner coordinates]]
    - only if objp!=[]: objp_confirmed: array of [3d corner coordinates]
    '''
    global old_image_path
    old_image_path = img_path
                                 
    def on_key(event):
        '''
        Handles key press events:
        'Y' to return imgp, 'N' to dismiss image, 'C' to click points by hand.
        Left click to add a point, 'H' to indicate it is not visible, right click to remove the last point.
        '''

        global imgp_confirmed, objp_confirmed, objp_confirmed_notok, scat, ax_3d, fig_3d, events, count
        
        if event.key == 'y':
            # If 'y', close all
            # If points have been clicked, imgp_confirmed is returned, else imgp
            # If objp is given, objp_confirmed is returned in addition
            if 'scat' not in globals() or 'imgp_confirmed' not in globals():
                imgp_confirmed = imgp
                objp_confirmed = objp
            else:
                imgp_confirmed = np.array([imgp.astype('float32') for imgp in imgp_confirmed])
                objp_confirmed = objp_confirmed
            # OpenCV needs at leas 4 correspondance points to calibrate
            if len(imgp_confirmed) < 6:
                objp_confirmed = []
                imgp_confirmed = []
            # close all, del all global variables except imgp_confirmed and objp_confirmed
            plt.close('all')
            if len(objp) == 0:
                if 'objp_confirmed' in globals():
                    del objp_confirmed

        if event.key == 'n' or event.key == 'q':
            # If 'n', close all and return nothing
            plt.close('all')
            imgp_confirmed = []
            objp_confirmed = []

        if event.key == 'c':
            # TODO: RIGHT NOW, IF 'C' IS PRESSED ANOTHER TIME, OBJP_CONFIRMED AND IMGP_CONFIRMED ARE RESET TO []
            # We should reopen a figure without point on it
            img_for_pointing = cv2.imread(old_image_path)
            if img_for_pointing is None:
                cap = cv2.VideoCapture(old_image_path)
                ret, img_for_pointing = cap.read()
            img_for_pointing = cv2.cvtColor(img_for_pointing, cv2.COLOR_BGR2RGB)
            ax.imshow(img_for_pointing)
            # To update the image
            plt.draw()

            if 'objp_confirmed' in globals():
                del objp_confirmed
            # If 'c', allows retrieving imgp_confirmed by clicking them on the image
            scat = ax.scatter([],[],s=100,marker='+',color='g')
            plt.connect('button_press_event', on_click)
            # If objp is given, display 3D object points in black
            if len(objp) != 0 and not plt.fignum_exists(2):
                fig_3d = plt.figure()
                fig_3d.tight_layout()
                fig_3d.canvas.manager.set_window_title('Object points to be clicked')
                ax_3d = fig_3d.add_subplot(projection='3d')
                plt.rc('xtick', labelsize=5)
                plt.rc('ytick', labelsize=5)
                for i, (xs,ys,zs) in enumerate(np.float32(objp)):
                    ax_3d.scatter(xs,ys,zs, marker='.', color='k')
                    ax_3d.text(xs,ys,zs,  f'{str(i+1)}', size=10, zorder=1, color='k') 
                set_axes_equal(ax_3d)
                ax_3d.set_xlabel('X')
                ax_3d.set_ylabel('Y')
                ax_3d.set_zlabel('Z')
                if np.all(objp[:,2] == 0):
                    ax_3d.view_init(elev=-90, azim=0)
                fig_3d.show()

        if event.key == 'h':
            # If 'h', indicates that one of the objp is not visible on image
            # Displays it in red on 3D plot
            if len(objp) != 0  and 'ax_3d' in globals():
                count = [0 if 'count' not in globals() else count+1][0]
                if 'events' not in globals():
                    # retrieve first objp_confirmed_notok and plot 3D
                    events = [event]
                    objp_confirmed_notok = objp[count]
                    ax_3d.scatter(*objp_confirmed_notok, marker='o', color='r')
                    fig_3d.canvas.draw()
                elif count == len(objp)-1:
                    # if all objp have been clicked or indicated as not visible, close all
                    objp_confirmed = np.array([[objp[count]] if 'objp_confirmed' not in globals() else objp_confirmed+[objp[count]]][0])[:-1]
                    imgp_confirmed = np.array(np.expand_dims(scat.get_offsets(), axis=1), np.float32) 
                    plt.close('all')
                    for var_to_delete in ['events', 'count', 'scat', 'fig_3d', 'ax_3d', 'objp_confirmed_notok']:
                        if var_to_delete in globals():
                            del globals()[var_to_delete]
                else:
                    # retrieve other objp_confirmed_notok and plot 3D
                    events.append(event)
                    objp_confirmed_notok = objp[count]
                    ax_3d.scatter(*objp_confirmed_notok, marker='o', color='r')
                    fig_3d.canvas.draw()
            else:
                pass


    def on_click(event):
        '''
        Detect click position on image
        If right click, last point is removed
        '''
        
        global imgp_confirmed, objp_confirmed, objp_confirmed_notok, events, count, xydata
        
        # Left click: Add clicked point to imgp_confirmed
        # Display it on image and on 3D plot
        if event.button == 1: 
            # To remember the event to cancel after right click
            if 'events' in globals():
                events.append(event)
            else:
                events = [event]

            # Add clicked point to image
            xydata = scat.get_offsets()
            new_xydata = np.concatenate((xydata,[[event.xdata,event.ydata]]))
            scat.set_offsets(new_xydata)
            imgp_confirmed = np.expand_dims(scat.get_offsets(), axis=1)    
            plt.draw()

            # Add clicked point to 3D object points if given
            if len(objp) != 0:
                count = [0 if 'count' not in globals() else count+1][0]
                if count==0:
                    # retrieve objp_confirmed and plot 3D
                    objp_confirmed = [objp[count]]
                    ax_3d.scatter(*objp[count], marker='o', color='g')
                    fig_3d.canvas.draw()
                elif count == len(objp)-1:
                    # close all
                    plt.close('all')
                    # retrieve objp_confirmed
                    objp_confirmed = np.array([[objp[count]] if 'objp_confirmed' not in globals() else objp_confirmed+[objp[count]]][0])
                    imgp_confirmed = np.array(imgp_confirmed, np.float32)
                    # delete all
                    for var_to_delete in ['events', 'count', 'scat', 'scat_3d', 'fig_3d', 'ax_3d', 'objp_confirmed_notok']:
                        if var_to_delete in globals():
                            del globals()[var_to_delete]
                else:
                    # retrieve objp_confirmed and plot 3D
                    objp_confirmed = [[objp[count]] if 'objp_confirmed' not in globals() else objp_confirmed+[objp[count]]][0]
                    ax_3d.scatter(*objp[count], marker='o', color='g')
                    fig_3d.canvas.draw()
                

        # Right click: 
        # If last event was left click, remove last point and if objp given, from objp_confirmed
        # If last event was 'H' and objp given, remove last point from objp_confirmed_notok
        elif event.button == 3: # right click
            if 'events' in globals():
                # If last event was left click: 
                if 'button' in dir(events[-1]):
                    if events[-1].button == 1: 
                        # Remove lastpoint from image
                        new_xydata = scat.get_offsets()[:-1]
                        scat.set_offsets(new_xydata)
                        plt.draw()
                        # Remove last point from imgp_confirmed
                        imgp_confirmed = imgp_confirmed[:-1]
                        if len(objp) != 0:
                            if count >= 0: 
                                count -= 1
                            # Remove last point from objp_confirmed
                            objp_confirmed = objp_confirmed[:-1]
                            # remove from plot 
                            if len(ax_3d.collections) > len(objp):
                                ax_3d.collections[-1].remove()
                                fig_3d.canvas.draw()
                            
                # If last event was 'h' key
                elif events[-1].key == 'h':
                    if len(objp) != 0:
                        if count >= 1: count -= 1
                        # Remove last point from objp_confirmed_notok
                        objp_confirmed_notok = objp_confirmed_notok[:-1]
                        # remove from plot  
                        if len(ax_3d.collections) > len(objp):
                            ax_3d.collections[-1].remove()
                            fig_3d.canvas.draw()                
    

    def set_axes_equal(ax):
        '''
        Make axes of 3D plot have equal scale so that spheres appear as spheres,
        cubes as cubes, etc.
        From https://stackoverflow.com/questions/13685386/how-to-set-the-equal-aspect-ratio-for-all-axes-x-y-z

        Input
        ax: a matplotlib axis, e.g., as output from plt.gca().
        '''

        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()

        x_range = abs(x_limits[1] - x_limits[0])
        x_middle = np.mean(x_limits)
        y_range = abs(y_limits[1] - y_limits[0])
        y_middle = np.mean(y_limits)
        z_range = abs(z_limits[1] - z_limits[0])
        z_middle = np.mean(z_limits)

        # The plot bounding box is a sphere in the sense of the infinity
        # norm, hence I call half the max range the plot radius.
        plot_radius = 0.5*max([x_range, y_range, z_range])

        ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
        ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
        ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

    # Write instructions
    cv2.putText(img, 'Type "Y" to accept point detection.', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, 'Type "Y" to accept point detection.', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, 'If points are wrongfully (or not) detected:', (20, 43), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, 'If points are wrongfully (or not) detected:', (20, 43), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, '- type "N" to dismiss this image,', (20, 66), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, '- type "N" to dismiss this image,', (20, 66), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, '- type "C" to click points by hand (beware of their order).', (20, 89), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, '- type "C" to click points by hand (beware of their order).', (20, 89), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, '   left click to add a point, right click to remove it, "H" to indicate it is not visible. ', (20, 112), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, '   left click to add a point, right click to remove it, "H" to indicate it is not visible. ', (20, 112), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, '   Confirm with "Y", cancel with "N".', (20, 135), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, '   Confirm with "Y", cancel with "N".', (20, 135), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    cv2.putText(img, 'Use mouse wheel to zoom in and out and to pan', (20, 158), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
    cv2.putText(img, 'Use mouse wheel to zoom in and out and to pan', (20, 158), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
    
    # Put image in a matplotlib figure for more controls
    plt.rcParams['toolbar'] = 'None'
    fig, ax = plt.subplots()
    fig = plt.gcf()
    fig.canvas.manager.set_window_title(os.path.basename(img_path))
    ax.axis("off")
    for corner in imgp:
        x, y = corner.ravel()
        cv2.drawMarker(img, (int(x),int(y)), (128,128,128), cv2.MARKER_CROSS, 10, 2)
    ax.imshow(img)
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    
    # Allow for zoom and pan in image
    zoom_factory(ax)
    ph = panhandler(fig, button=2)

    # Handles key presses to Accept, dismiss, or click points by hand
    cid = fig.canvas.mpl_connect('key_press_event', on_key)
    
    plt.draw()
    plt.show(block=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.rcParams['toolbar'] = 'toolmanager'

    for var_to_delete in ['events', 'count', 'scat', 'fig_3d', 'ax_3d', 'objp_confirmed_notok']:
        if var_to_delete in globals():
            del globals()[var_to_delete]

    if 'imgp_confirmed' in globals() and 'objp_confirmed' in globals():
        return imgp_confirmed, objp_confirmed
    elif 'imgp_confirmed' in globals() and not 'objp_confirmed' in globals():
        return imgp_confirmed
    else:
        return



def trc_write(object_coords_3d, trc_path):
    '''
    Make Opensim compatible trc file from a dataframe with 3D coordinates

    INPUT:
    - object_coords_3d: list of 3D point lists
    - trc_path: output path of the trc file

    OUTPUT:
    - trc file with 2 frames of the same 3D points
    '''

    #Header
    DataRate = CameraRate = OrigDataRate = 1
    NumFrames = 2
    NumMarkers = len(object_coords_3d)
    keypoints_names = np.arange(NumMarkers)
    header_trc = ['PathFileType\t4\t(X/Y/Z)\t' + os.path.basename(trc_path), 
            'DataRate\tCameraRate\tNumFrames\tNumMarkers\tUnits\tOrigDataRate\tOrigDataStartFrame\tOrigNumFrames', 
            '\t'.join(map(str,[DataRate, CameraRate, NumFrames, NumMarkers, 'm', OrigDataRate, NumFrames])),
            'Frame#\tTime\t' + '\t\t\t'.join(str(k) for k in keypoints_names) + '\t\t',
            '\t\t'+'\t'.join([f'X{i+1}\tY{i+1}\tZ{i+1}' for i in range(NumMarkers)])]
    
    # Zup to Yup coordinate system
    object_coords_3d = pd.DataFrame([np.array(object_coords_3d).flatten(), np.array(object_coords_3d).flatten()])
    object_coords_3d = zup2yup(object_coords_3d)
    
    #Add Frame# and Time columns
    object_coords_3d.index = np.array(range(0, NumFrames)) + 1
    object_coords_3d.insert(0, 't', object_coords_3d.index / DataRate)

    #Write file
    with open(trc_path, 'w') as trc_o:
        [trc_o.write(line+'\n') for line in header_trc]
        object_coords_3d.to_csv(trc_o, sep='\t', index=True, header=None, lineterminator='\n')

    return trc_path


def toml_write(calib_path, C, S, D, K, R, T):
    '''
    Writes calibration parameters to a .toml file

    INPUTS:
    - calib_path: path to the output calibration file: string
    - C: camera name: list of strings
    - S: image size: list of list of floats
    - D: distorsion: list of arrays of floats
    - K: intrinsic parameters: list of 3x3 arrays of floats
    - R: extrinsic rotation: list of arrays of floats (Rodrigues)
    - T: extrinsic translation: list of arrays of floats

    OUTPUTS:
    - a .toml file cameras calibrations
    '''

    with open(os.path.join(calib_path), 'w+') as cal_f:
        for c in range(len(C)):
            cam=f'[{C[c]}]\n'
            name = f'name = "{C[c]}"\n'
            size = f'size = [ {S[c][0]}, {S[c][1]}]\n' 
            mat = f'matrix = [ [ {K[c][0,0]}, 0.0, {K[c][0,2]}], [ 0.0, {K[c][1,1]}, {K[c][1,2]}], [ 0.0, 0.0, 1.0]]\n'
            dist = f'distortions = [ {D[c][0]}, {D[c][1]}, {D[c][2]}, {D[c][3]}]\n' 
            rot = f'rotation = [ {R[c][0]}, {R[c][1]}, {R[c][2]}]\n'
            tran = f'translation = [ {T[c][0]}, {T[c][1]}, {T[c][2]}]\n'
            fish = f'fisheye = false\n\n'
            cal_f.write(cam + name + size + mat + dist + rot + tran + fish)
        meta = '[metadata]\nadjusted = false\nerror = 0.0\n'
        cal_f.write(meta)


def calibrate_extrinsics(calib_dir, extrinsics_config_dict, C, S, K, D):
    '''
    Calibrates extrinsic parameters
    from an image or the first frame of a video
    of a checkerboard or of measured clues on the scene

    INPUTS:
    - calib_dir: directory containing intrinsic and extrinsic folders, each populated with camera directories
    - extrinsics_config_dict: dictionary of extrinsics parameters (extrinsics_method, calculate_extrinsics, show_detection_extrinsics, extrinsics_extension, extrinsics_corners_nb, extrinsics_square_size, extrinsics_marker_size, extrinsics_aruco_dict, object_coords_3d)

    OUTPUTS:
    - R: extrinsic rotation: list of arrays of floats (Rodrigues)
    - T: extrinsic translation: list of arrays of floats
    '''

    try:
        extrinsics_cam_listdirs_names = sorted(next(os.walk(os.path.join(calib_dir, 'extrinsics')))[1])
    except StopIteration:
        logging.exception(f'Error: No {os.path.join(calib_dir, "extrinsics")} folder found.')
        raise Exception(f'Error: No {os.path.join(calib_dir, "extrinsics")} folder found.')
    
    extrinsics_method = extrinsics_config_dict.get('extrinsics_method')
    ret, R, T = [], [], []
    
    if extrinsics_method in {'board', 'scene'}:
                
        # Define 3D object points
        if extrinsics_method == 'board':
            extrinsics_corners_nb = extrinsics_config_dict.get('board').get('extrinsics_corners_nb')
            extrinsics_square_size = extrinsics_config_dict.get('board').get('extrinsics_square_size') / 1000 # convert to meters
            object_coords_3d = np.zeros((extrinsics_corners_nb[0] * extrinsics_corners_nb[1], 3), np.float32)
            object_coords_3d[:, :2] = np.mgrid[0:extrinsics_corners_nb[0], 0:extrinsics_corners_nb[1]].T.reshape(-1, 2)
            object_coords_3d[:, :2] = object_coords_3d[:, 0:2] * extrinsics_square_size
        elif extrinsics_method == 'scene':
            object_coords_3d = np.array(extrinsics_config_dict.get('scene').get('object_coords_3d'), np.float32)
                
        # Save reference 3D coordinates as trc
        calib_output_path = os.path.join(calib_dir, f'Object_points.trc')
        trc_write(object_coords_3d, calib_output_path)
    
        for i, cam in enumerate(extrinsics_cam_listdirs_names):
            logging.info(f'\nCamera {cam}:')
            
            # Read images or video
            extrinsics_extension = [extrinsics_config_dict.get('board').get('extrinsics_extension') if extrinsics_method == 'board'
                                    else extrinsics_config_dict.get('scene').get('extrinsics_extension')][0]
            show_reprojection_error = [extrinsics_config_dict.get('board').get('show_reprojection_error') if extrinsics_method == 'board'
                                    else extrinsics_config_dict.get('scene').get('show_reprojection_error')][0]
            img_vid_files = glob.glob(os.path.join(calib_dir, 'extrinsics', cam, f'*.{extrinsics_extension}'))
            if len(img_vid_files) == 0:
                logging.exception(f'The folder {os.path.join(calib_dir, "extrinsics", cam)} does not exist or does not contain any files with extension .{extrinsics_extension}.')
                raise ValueError(f'The folder {os.path.join(calib_dir, "extrinsics", cam)} does not exist or does not contain any files with extension .{extrinsics_extension}.')
            img_vid_files = sorted(img_vid_files, key=lambda c: [int(n) for n in re.findall(r'\d+', c)]) #sorting paths with numbers
            
            # extract frames from image, or from video if imread is None
            img = cv2.imread(img_vid_files[0])
            if img is None:
                cap = cv2.VideoCapture(img_vid_files[0])
                res, img = cap.read()
                if res == False:
                    raise
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Find corners or label by hand
            if extrinsics_method == 'board':
                imgp, objp = findCorners(img_vid_files[0], extrinsics_corners_nb, objp=object_coords_3d, show=show_reprojection_error)
                if len(imgp) == 0:
                    logging.exception('No corners found. Set "show_detection_extrinsics" to true to click corners by hand, or change extrinsic_board_type to "scene"')
                    raise ValueError('No corners found. Set "show_detection_extrinsics" to true to click corners by hand, or change extrinsic_board_type to "scene"')

            elif extrinsics_method == 'scene':
                imgp, objp = imgp_objp_visualizer_clicker(img, imgp=[], objp=object_coords_3d, img_path=img_vid_files[0])
                if len(imgp) == 0:
                    logging.exception('No points clicked (or fewer than 6). Press \'C\' when the image is displayed, and then click on the image points corresponding to the \'object_coords_3d\' you measured and wrote down in the Config.toml file.')
                    raise ValueError('No points clicked (or fewer than 6). Press \'C\' when the image is displayed, and then click on the image points corresponding to the \'object_coords_3d\' you measured and wrote down in the Config.toml file.')
                if len(objp) < 10:
                    logging.info(f'Only {len(objp)} reference points for camera {cam}. Calibration of extrinsic parameters may not be accurate with fewer than 10 reference points, as spread out in the captured volume as possible.')
            
            elif extrinsics_method == 'keypoints':
                logging.info('Calibration based on keypoints is not available yet.')
            
            # Calculate extrinsics
            mtx, dist = np.array(K[i]), np.array(D[i])
            _, r, t = cv2.solvePnP(np.array(objp)*1000, imgp, mtx, dist)
            r, t = r.flatten(), t.flatten()
            t /= 1000 

            # Projection of object points to image plane
            # # Former way, distortions used to be ignored
            # Kh_cam = np.block([mtx, np.zeros(3).reshape(3,1)])
            # r_mat, _ = cv2.Rodrigues(r)
            # H_cam = np.block([[r_mat,t.reshape(3,1)], [np.zeros(3), 1 ]])
            # P_cam = Kh_cam @ H_cam
            # proj_obj = [ ( P_cam[0] @ np.append(o, 1) /  (P_cam[2] @ np.append(o, 1)),  P_cam[1] @ np.append(o, 1) /  (P_cam[2] @ np.append(o, 1)) ) for o in objp]
            proj_obj = np.squeeze(cv2.projectPoints(objp,r,t,mtx,dist)[0])

            # Check calibration results
            if show_reprojection_error:
                # Reopen image, otherwise 2 sets of text are overlaid
                img = cv2.imread(img_vid_files[0])
                if img is None:
                    cap = cv2.VideoCapture(img_vid_files[0])
                    res, img = cap.read()
                    if res == False:
                        raise
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                for o in proj_obj:
                    cv2.circle(img, (int(o[0]), int(o[1])), 8, (0,0,255), -1) 
                for i in imgp:
                    cv2.drawMarker(img, (int(i[0][0]), int(i[0][1])), (0,255,0), cv2.MARKER_CROSS, 15, 2)
                cv2.putText(img, 'Verify calibration results, then close window.', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
                cv2.putText(img, 'Verify calibration results, then close window.', (20, 20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA) 
                cv2.drawMarker(img, (20,40), (0,255,0), cv2.MARKER_CROSS, 15, 2)
                cv2.putText(img, '    Clicked points', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
                cv2.putText(img, '    Clicked points', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
                cv2.circle(img, (20,60), 8, (0,0,255), -1)    
                cv2.putText(img, '    Reprojected object points', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 7, lineType = cv2.LINE_AA)
                cv2.putText(img, '    Reprojected object points', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,0), 2, lineType = cv2.LINE_AA)    
                im_pil = Image.fromarray(img)
                im_pil.show(title = os.path.basename(img_vid_files[0]))

            # Calculate reprojection error
            imgp_to_objreproj_dist = [euclidean_distance(proj_obj[n], imgp[n]) for n in range(len(proj_obj))]
            rms_px = np.sqrt(np.sum([d**2 for d in imgp_to_objreproj_dist]))
            ret.append(rms_px)
            R.append(r)
            T.append(t)
        
    elif extrinsics_method == 'keypoints':
        raise NotImplementedError('This has not been integrated yet.')
    
    else:
        raise ValueError('Wrong value for extrinsics_method')

    return ret, C, S, D, K, R, T

def parse_timestamp(filename):
    """Extracts and converts timestamp from filename to a datetime object."""
    match = trial_pattern.search(filename)
    if match:
        timestamp_str = match.group(1)
        return datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    return None

def get_camera_number(filename):
    """Extracts camera number from the filename."""
    match = trial_pattern.search(filename)
    if match:
        return match.group(2)
    return None

def group_videos_by_trial(video_files, time_tolerance=5):
    """Groups videos into trials allowing a ±time_tolerance seconds difference."""
    trials = []
    video_data = [(file, parse_timestamp(file)) for file in video_files]
    video_data = [v for v in video_data if v[1] is not None]
    video_data.sort(key=lambda x: x[1])

    current_trial = []
    for video, timestamp in video_data:
        if not current_trial:
            current_trial.append((video, timestamp))
        else:
            last_timestamp = current_trial[-1][1]
            if abs((timestamp - last_timestamp).total_seconds()) <= time_tolerance:
                current_trial.append((video, timestamp))
            else:
                trials.append(current_trial)
                current_trial = [(video, timestamp)]

    if current_trial:
        trials.append(current_trial)

    return trials


# Define the trial pattern to extract timestamp and camera number
trial_pattern = re.compile(r"(\d{8}_\d{6})-CAMERA(\d+)-")


if __name__ == "__main__":
    
    source_Videos_folder = r"C:\videos\DCIM\3"
    # === SET THIS TO YOUR PROJECT DIRECTORY ===
    VideoExtrisic_destination_root = r"C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Extrinsic_Calib\Pose2Sim_Folder_Struct\calibration\extrinsics"
    project_dir = r'C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Extrinsic_Calib\Pose2Sim_Folder_Struct'  # Example: r'C:\Users\you\Videos\MyProject'
    
    # === CLEAN OUT EXISTING FOLDERS/FILES in VideoExtrisic_destination_root ===
    if os.path.exists(VideoExtrisic_destination_root):
        for item in os.listdir(VideoExtrisic_destination_root):
            item_path = os.path.join(VideoExtrisic_destination_root, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"❌ Failed to delete {item_path}: {e}")
    else:
        os.makedirs(VideoExtrisic_destination_root)
        
    # Display trials for user to choose
    video_files = [os.path.join(source_Videos_folder, f) for f in os.listdir(source_Videos_folder) if f.endswith(".MP4")]
    trials = group_videos_by_trial(video_files)
    print("\nWhich was is the calibration trial in the source_videos_file Available Trials:")
    for idx, trial in enumerate(trials):
        trial_name = parse_timestamp(trial[0][0]).strftime("%Y%m%d_%H%M%S")
        print(f"[{idx}] Trial {trial_name} with {len(trial)} video(s)")


    selected_idx = int(input("\nEnter the index of the calibration trial: "))
    calibration_trial = trials[selected_idx]

    # Copy videos to corresponding ext_camXX folders
    for video_path, _ in calibration_trial:
        cam_num = get_camera_number(video_path)
        if cam_num:
            dest_folder = os.path.join(VideoExtrisic_destination_root, f"ext_cam{cam_num.zfill(2)}")
            os.makedirs(dest_folder, exist_ok=True)
            shutil.copy(video_path, dest_folder)
            print(f"✅ Copied {os.path.basename(video_path)} to {dest_folder}")
        else:
            print(f"⚠️ Could not determine camera number for {video_path}")
    
        
    # Locate and load the Config.toml file
    config_path = os.path.join(project_dir, 'Config.toml')
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Could not find Config.toml in {project_dir}")
    config_dict = toml.load(config_path)
    
    # Extract calibration config
    calib_dir = os.path.join(project_dir, 'calibration')
    intrinsics_config = config_dict['calibration']['calculate']['intrinsics']
    extrinsics_config = config_dict['calibration']['calculate']['extrinsics']
    
    
    # Enable extrinsic calculation via scene labeling
    extrinsics_config['calculate_extrinsics'] = True
    extrinsics_config['extrinsics_method'] = 'scene'
    
    # Optional: enable logging
    logging.basicConfig(level=logging.INFO)
    
    # Run calibration
    print("Starting extrinsic calibration...")
    ret, C, S, D, K, R, T = calib_calc_fun(calib_dir, intrinsics_config, extrinsics_config)
    print("Calibration complete.")
    
