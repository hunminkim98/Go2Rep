# Go2Rep/tools/report_generator.py

import numpy as np
import pandas as pd
from TheiaReader import TheiaReader
from scipy.spatial.transform import Rotation as R
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import json
import tkinter as tk
from tkinter import filedialog

import tkinter as tk
from tkinter import filedialog, ttk, messagebox

def generate_report(c3d_path=None, json_path=None, output_dir=None,
                    default_length=0, euler_seq='xyz',**kwargs):
    if c3d_path is None or json_path is None or output_dir is None:
        # Open popup to collect paths from the user
        popup = tk.Toplevel()
        popup.title("Select Report Files and Output Directory")
        popup.geometry("800x250")
        popup.grab_set()  # Lock focus on this popup window

        def browse_file(var, filetypes):
            filepath = filedialog.askopenfilename(filetypes=filetypes)
            if filepath:
                var.set(filepath)

        def browse_folder(var):
            folderpath = filedialog.askdirectory()
            if folderpath:
                var.set(folderpath)

        def run_report():
            c3d = c3d_var.get()
            jsn = json_var.get()
            out = out_var.get()
            if not (c3d and jsn and out):
                messagebox.showerror("Missing Input", "Please provide all required paths.")
                return
            popup.destroy()  # Close popup
            # Call same function again with actual paths
            generate_report(c3d_path=c3d, json_path=jsn, output_dir=out, **kwargs)

        c3d_var = tk.StringVar()
        json_var = tk.StringVar()
        out_var = tk.StringVar()

        for i, (label, var, filetype, browse_func) in enumerate([
            ("C3D File:", c3d_var, [('C3D files', '*.c3d')], lambda: browse_file(c3d_var, [('C3D files', '*.c3d')])),
            ("JSON File:", json_var, [('JSON files', '*.json')], lambda: browse_file(json_var, [('JSON files', '*.json')])),
            ("Output Directory:", out_var, None, lambda: browse_folder(out_var))
        ]):
            frame = ttk.Frame(popup)
            frame.pack(fill="x", pady=5, padx=10)
            ttk.Label(frame, text=label, width=20).pack(side="left")
            ttk.Entry(frame, textvariable=var, width=50).pack(side="left", padx=5)
            ttk.Button(frame, text="Browse", command=browse_func).pack(side="left")

        ttk.Button(popup, text="Generate Report", command=run_report).pack(pady=20)
        return  # Don’t continue until user finishes popup

    # --- Proceed with report logic now that paths are collected ---
    output_trc = os.path.join(output_dir, 'distal_points_all_segments.trc')
    output_angles_csv = os.path.join(output_dir, 'joint_angles.csv')
    pdf_output_path = os.path.join(output_dir, 'joint_angles_plots.pdf')
    
    joint_pairs = {
        'pelvis': ['torso', 'l_thigh', 'r_thigh'],
        'torso': ['head', 'l_uarm', 'r_uarm'],
        'l_uarm': ['l_larm'],
        'l_larm': ['l_hand'],
        'r_uarm': ['r_larm'],
        'r_larm': ['r_hand'],
        'l_thigh': ['l_shank'],
        'l_shank': ['l_foot'],
        'l_foot': ['l_toes'],
        'r_thigh': ['r_shank'],
        'r_shank': ['r_foot'],
        'r_foot': ['r_toes']
    }
    # breakpoint()
    # with open(json_path, 'r') as f:
    #     json_data = json.load(f)  
    import re

    # Fallback if full JSON parsing fails
    segment_lengths_fallback = {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to extract segment entries with "name" and "length" using regex
    segments_match = re.search(r'"segments"\s*:\s*\[(.*?)\](,|\s*})', content, re.DOTALL)
    if segments_match:
        segments_str = segments_match.group(1)
        segment_entries = re.finditer(r'{.*?}', segments_str, re.DOTALL)
    
        for entry in segment_entries:
            try:
                segment_data = json.loads(entry.group())
                name = segment_data.get("name", "")
                length = segment_data.get("length", None)
                if name and length is not None:
                    segment_lengths_fallback[name] = float(length)
            except json.JSONDecodeError:
                continue
    else:
        print("⚠️ Could not extract any segments from JSON.")
    reader = TheiaReader.TheiaReader(c3d_path)
    header_info = reader.header
    fps = header_info.get('frame_rate', 100)
    
    label_list = list(reader.rotations.keys())
    # Detect prefix dynamically
    prefix_candidates = [lbl.split(':')[0] for lbl in label_list if ':' in lbl]
    subject_prefix = prefix_candidates[0] if prefix_candidates else ''
    
    # Now filter based on detected or empty prefix
    if subject_prefix:
        segment_labels = [lbl for lbl in label_list if lbl.startswith(subject_prefix + ':') and lbl.endswith('_4X4')]
        segment_names = [lbl.split(':')[1].replace('_4X4', '') for lbl in segment_labels]
    else:
        segment_labels = [lbl for lbl in label_list if lbl.endswith('_4X4')]
        segment_names = [lbl.replace('_4X4', '') for lbl in segment_labels]
    n_frames = int(header_info.get('last_frame', reader.rotations[segment_labels[0]].values.shape[0]))
    try:
        H_matrices = {seg: reader.rotations[f'{subject_prefix}:{seg}_4X4'].values for seg in segment_names}
    except:
        H_matrices = {}
        for seg in segment_names:
            key = f'{subject_prefix + ":" if subject_prefix else ""}{seg}_4X4'
            if key in reader.rotations:
                H_matrices[seg] = reader.rotations[key].values
            else:
                print(f"⚠️ Warning: Rotation key '{key}' not found in reader.")
    def get_origin(T): return T[:, :3, 3]

    lengths = {}
    for seg in segment_names:
        segment_length = None
        length_param_name = f'{subject_prefix}:{seg.upper()}_LENGTH'
        for group in reader.parameters_group.values():
            if group['name'] == 'THEIA3D' and length_param_name in group['parameters']:
                try:
                    segment_length = float(group['parameters'][length_param_name]['value'])
                except ValueError:
                    pass
                break
        # if segment_length is None:
        #     try:
        #         segment_info = next((s for s in json_data['data']['subjects'][0]['segments'] if s['name'] == seg), None)
        #         if segment_info:
        #             segment_length = float(segment_info.get('length', None))
        #     except Exception:
        #         pass
        if segment_length is None:
            segment_length = segment_lengths_fallback.get(seg, None)
        if segment_length is not None:
            lengths[seg] = np.full(n_frames, segment_length)
        else:
            origin = get_origin(H_matrices[seg])
            if seg in joint_pairs:
                for child in joint_pairs[seg]:
                    if child in H_matrices:
                        origin_p = get_origin(H_matrices[seg])
                        origin_c = get_origin(H_matrices[child])
                        lengths[seg] = np.linalg.norm(origin_c - origin_p, axis=1)
            # fallback: calculate length from H_matrices
            if segment_length is None:
                if seg in joint_pairs:
                    for child in joint_pairs[seg]:
                        if child in H_matrices:
                            origin_parent = get_origin(H_matrices[seg])
                            origin_child = get_origin(H_matrices[child])
                            length_array = np.linalg.norm(origin_child - origin_parent, axis=1)
                            lengths[seg] = length_array
                            break  # found a valid child, break
                else:
                    lengths[seg] = np.full(n_frames, default_length)
    distal_points = {seg: [] for seg in segment_names}
    
    for i in range(n_frames):
        for seg in segment_names:
            if seg == 'pelvis':
                continue  # Skip pelvis entirely
    
            T = H_matrices[seg][i]
    
            # Handle special length rules
            if seg == 'l_hand':
                L = lengths['l_larm'][i]
            elif seg == 'r_hand':
                L = lengths['r_larm'][i]
            elif seg in ['l_toes', 'r_toes']:
                L = 0.0
            else:
                L = lengths[seg][i]
    
            distal = (T @ np.array([0, 0, -L, 1]))[:3]
            distal_points[seg].append(distal)
    
    distal_points = {k: np.vstack(v) for k, v in distal_points.items() if len(v) > 0}


    def write_trc(filename, points, fps):
        n_frames = next(iter(points.values())).shape[0]
        labels = list(points.keys())
        header = [
            "PathFileType\t4\t(X/Y/Z)\t" + os.path.basename(filename),
            f"DataRate\tCameraRate\tNumFrames\tNumMarkers\tUnits\tOrigDataRate\tOrigDataStartFrame\tOrigNumFrames",
            f"{fps}\t{fps}\t{n_frames}\t{len(labels)}\tm\t{fps}\t1\t{n_frames}",
            "Frame#\tTime\t" + '\t'.join([f"{label}\t\t" for label in labels]),
            "\t\t" + '\t'.join([f"X{i+1}\tY{i+1}\tZ{i+1}" for i in range(len(labels))])
        ]
        rows = []
        for i in range(n_frames):
            row = [str(i + 1), f"{i / fps:.5f}"]
            for label in labels:
                xyz = points[label][i]
                for val in xyz:
                    if np.isnan(val):
                        row.append("")  # Leave blank if NaN
                    else:
                        row.append(f"{val:.3f}")
            rows.append('\t'.join(row))
        with open(filename, 'w') as f:
            f.write('\n'.join(header + rows))
    
    # Save TRC file
    write_trc(output_trc, distal_points, fps)
    
    def compute_joint_angles(R_parent, R_child):
        R_rel = R_parent.T @ R_child
        return R.from_matrix(R_rel).as_euler(euler_seq, degrees=True)

    angles_dict = {}
    for parent, children in joint_pairs.items():
        if parent not in H_matrices:
            continue
        for child in children:
            if child not in H_matrices:
                continue
            joint_name = f"{parent}_{child}"
            angles = []
            for i in range(n_frames):
                R_p = H_matrices[parent][i][:3, :3]
                R_c = H_matrices[child][i][:3, :3]
    
                if np.isnan(R_p).any() or np.isnan(R_c).any():
                    angles.append(np.full((3,), np.nan))  # Use NaN triplet
                    continue
    
                try:
                    angle = compute_joint_angles(R_p, R_c)
                    angles.append(angle)
                except:
                    angles.append(np.full((3,), np.nan))  # Also put NaNs on error
    
            angles_dict[joint_name] = np.vstack(angles)

    angle_df = pd.DataFrame()
    angle_df['Frame'] = np.arange(1, n_frames + 1)
    angle_df['Time'] = angle_df['Frame'] / fps
    for joint, angles in angles_dict.items():
        angle_df[f'{joint}_X'] = angles[:, 0]
        angle_df[f'{joint}_Y'] = angles[:, 1]
        angle_df[f'{joint}_Z'] = angles[:, 2]
    angle_df.to_csv(output_angles_csv, index=False)

    plots_per_page = 6
    cols, rows = 2, plots_per_page // 2
    joint_names = list(angles_dict.keys())

    with PdfPages(pdf_output_path) as pdf:
        for i in range(0, len(joint_names), plots_per_page):
            fig, axs = plt.subplots(rows, cols, figsize=(12, 8))
            axs = axs.flatten()
            for j, joint in enumerate(joint_names[i:i + plots_per_page]):
                ax = axs[j]
                angles = angles_dict[joint]
                time = np.arange(n_frames) / fps
                ax.plot(time, angles[:, 0], label='X')
                ax.plot(time, angles[:, 1], label='Y')
                ax.plot(time, angles[:, 2], label='Z')
                ax.set_title(joint)
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Angle (deg)')
                ax.legend()
                ax.grid(True)
            for j in range(len(joint_names[i:i + plots_per_page]), len(axs)):
                fig.delaxes(axs[j])
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

if __name__ == "__main__":
    try:
        # Replace these with your own paths
        c3d_path = r"C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Report_Generator\Drafts\Pose_filt.c3d"
        json_path = r"C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Report_Generator\Drafts\Pose.json"
        output_dir = r"C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Report_Generator\Drafts"
        
        generate_report(c3d_path, json_path, output_dir)
        print("✅ Report generation completed.")
    except Exception as e:
        print(f"❌ Report generation failed: {e}")