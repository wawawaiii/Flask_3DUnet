import torch
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('agg')  # GUI 백엔드를 사용하지 않도록 설정
import matplotlib.pyplot as plt
from skimage.util import montage
import io
import base64
import plotly.graph_objects as go

def load_nifti_image(file_path):
    img = nib.load(file_path)
    img_data = np.asarray(img.dataobj)
    img_data = np.rot90(img_data, k=3)
    return img_data

def save_nifti_image(data, file_path):
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, file_path)

def predict(model, images_tensor):
    with torch.no_grad():
        logits = model(images_tensor)
        probabilities = torch.sigmoid(logits)
        predictions = (probabilities >= 0.5).float()
    return predictions


def plot_prediction(flair_img, predictions):
    predictions_np = predictions.squeeze().cpu().numpy()
    predictions_np = np.moveaxis(predictions_np, (0, 1, 2, 3), (0, 3, 2, 1))
    mask_WT = np.rot90(montage(predictions_np[0]))
    mask_TC = np.rot90(montage(predictions_np[1]))
    mask_ET = np.rot90(montage(predictions_np[2]))

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.imshow(np.rot90(montage(flair_img)), cmap='bone')
    ax.imshow(np.ma.masked_where(mask_WT == False, mask_WT), cmap='cool', alpha=0.6)
    ax.imshow(np.ma.masked_where(mask_TC == False, mask_TC), cmap='autumn_r', alpha=0.6)
    ax.imshow(np.ma.masked_where(mask_ET == False, mask_ET), cmap='autumn', alpha=0.6)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    img_bytes = buf.read()
    img_base64 = base64.b64encode(img_bytes).decode('ascii')
    return img_base64


def plot_3d(flair_img, predictions):
    predictions_np = predictions.squeeze().cpu().numpy()

    # 3D scatter plot data for FLAIR image
    x_flair, y_flair, z_flair = np.where(flair_img > 0)
    flair_values = flair_img[x_flair, y_flair, z_flair]

    trace_flair = go.Scatter3d(
        x=x_flair, y=y_flair, z=z_flair,
        mode='markers',
        marker=dict(size=2, color=flair_values, colorscale='Gray', opacity=0.1),
        name='FLAIR Image'
    )

    # 3D scatter plot data for each tumor region
    x_wt, y_wt, z_wt = np.where(predictions_np[0] > 0)
    x_tc, y_tc, z_tc = np.where(predictions_np[1] > 0)
    x_et, y_et, z_et = np.where(predictions_np[2] > 0)

    trace_wt = go.Scatter3d(
        x=x_wt, y=y_wt, z=z_wt,
        mode='markers',
        marker=dict(size=3, color='blue', opacity=0.7),
        name='Whole Tumor'
    )

    trace_tc = go.Scatter3d(
        x=x_tc, y=y_tc, z=z_tc,
        mode='markers',
        marker=dict(size=3, color='red', opacity=0.7),
        name='Tumor Core'
    )

    trace_et = go.Scatter3d(
        x=x_et, y=y_et, z=z_et,
        mode='markers',
        marker=dict(size=3, color='green', opacity=0.7),
        name='Enhancing Tumor'
    )

    layout = go.Layout(
        title='3D Brain Tumor Segmentation',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data'
        )
    )

    fig = go.Figure(data=[trace_flair, trace_wt, trace_tc, trace_et], layout=layout)
    return fig.to_html(full_html=False)
