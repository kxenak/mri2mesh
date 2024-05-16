import SimpleITK as sitk
import numpy as np
import vtk
from vtk.util import numpy_support
import argparse
import os

def load_mri_image(file_path):  # Load MRI image
    image = sitk.ReadImage(file_path)  # Read image
    return image

def preprocess_image(image):  # Normalize MRI image
    image_array = sitk.GetArrayFromImage(image)  # Convert to array
    image_array = (image_array - np.min(image_array)) / (np.max(image_array) - np.min(image_array))  # Normalize
    return sitk.GetImageFromArray(image_array)  # Convert back to image

def segment_lungs(image, threshold=None):  # Segment lungs
    image_array = sitk.GetArrayFromImage(image)  # Convert to array
    if threshold is None:  # Use Otsu's method if no threshold provided
        otsu_filter = sitk.OtsuThresholdImageFilter()  # Otsu filter
        segmented_image = otsu_filter.Execute(image)  # Apply filter
    else:  # Use fixed threshold
        segmented_array = (image_array > threshold).astype(np.uint8)  # Thresholding
        segmented_image = sitk.GetImageFromArray(segmented_array)  # Convert back to image
    return segmented_image

def create_3d_mesh(segmented_image):  # Create 3D mesh
    vtk_data = numpy_support.numpy_to_vtk(sitk.GetArrayFromImage(segmented_image).flatten(), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)  # Convert to VTK array
    vtk_image = vtk.vtkImageData()  # Initialize VTK image
    vtk_image.SetDimensions(segmented_image.GetSize()[::-1])  # Set dimensions
    vtk_image.GetPointData().SetScalars(vtk_data)  # Set scalars

    marching_cubes = vtk.vtkMarchingCubes()  # Marching cubes
    marching_cubes.SetInputData(vtk_image)  # Set input
    marching_cubes.SetValue(0, 1)  # Set threshold
    marching_cubes.Update()  # Update

    mesh = marching_cubes.GetOutput()  # Get mesh
    return mesh, marching_cubes

def save_mesh(mesh, output_file):  # Save 3D mesh
    os.makedirs('generated_mesh', exist_ok=True)  # Create directory if it doesn't exist
    output_path = os.path.join('generated_mesh', output_file)  # Output path
    writer = vtk.vtkPLYWriter()  # PLY writer
    writer.SetFileName(output_path)  # Set file name
    writer.SetInputData(mesh)  # Set input
    writer.Write()  # Write to file

def visualize_mesh(mesh, marching_cubes):  # Visualize 3D mesh
    mapper = vtk.vtkPolyDataMapper()  # Mapper
    mapper.SetInputData(mesh)  # Set input

    actor = vtk.vtkActor()  # Actor
    actor.SetMapper(mapper)  # Set mapper

    renderer = vtk.vtkRenderer()  # Renderer
    render_window = vtk.vtkRenderWindow()  # Render window
    render_window.AddRenderer(renderer)  # Add renderer
    render_window_interactor = vtk.vtkRenderWindowInteractor()  # Interactor
    render_window_interactor.SetRenderWindow(render_window)  # Set render window

    renderer.AddActor(actor)  # Add actor
    renderer.SetBackground(0.1, 0.2, 0.3)  # Set background color

    slider_rep = vtk.vtkSliderRepresentation2D()  # Slider representation
    slider_rep.SetMinimumValue(0.0)  # Min value
    slider_rep.SetMaximumValue(1.0)  # Max value
    slider_rep.SetValue(0.5)  # Initial value
    slider_rep.SetTitleText("Threshold")  # Title
    slider_rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()  # Set coordinate system
    slider_rep.GetPoint1Coordinate().SetValue(0.1, 0.9)  # Set position
    slider_rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()  # Set coordinate system
    slider_rep.GetPoint2Coordinate().SetValue(0.4, 0.9)  # Set position
    slider_rep.SetSliderLength(0.02)  # Slider length
    slider_rep.SetSliderWidth(0.03)  # Slider width
    slider_rep.SetEndCapLength(0.01)  # End cap length
    slider_rep.SetEndCapWidth(0.03)  # End cap width
    slider_rep.SetTubeWidth(0.005)  # Tube width
    slider_rep.SetLabelFormat("%0.2f")  # Label format
    slider_rep.SetTitleHeight(0.02)  # Title height
    slider_rep.SetLabelHeight(0.02)  # Label height

    slider_widget = vtk.vtkSliderWidget()  # Slider widget
    slider_widget.SetInteractor(render_window_interactor)  # Set interactor
    slider_widget.SetRepresentation(slider_rep)  # Set representation
    slider_widget.SetAnimationModeToAnimate()  # Set animation mode

    def slider_callback(obj, event):  # Slider callback
        value = obj.GetRepresentation().GetValue()  # Get value
        marching_cubes.SetValue(0, value)  # Set threshold
        marching_cubes.Update()  # Update
        render_window.Render()  # Render

    slider_widget.AddObserver("InteractionEvent", slider_callback)  # Add observer

    render_window.Render()  # Render
    slider_widget.EnabledOn()  # Enable widget
    render_window_interactor.Start()  # Start interaction

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a 3D mesh of lungs from an MRI image.")  # Argument parser
    parser.add_argument("input_file", type=str, help="Path to the input MRI image file.")  # Input file argument
    parser.add_argument("output_file", type=str, help="Name of the output 3D mesh file.")  # Output file argument
    parser.add_argument("--threshold", type=float, default=None, help="Threshold value for segmentation. Use None for Otsu's method.")  # Threshold argument
    args = parser.parse_args()  # Parse arguments

    mri_image = load_mri_image(args.input_file)  # Load MRI image
    preprocessed_image = preprocess_image(mri_image)  # Preprocess image
    segmented_image = segment_lungs(preprocessed_image, args.threshold)  # Segment lungs
    mesh, marching_cubes = create_3d_mesh(segmented_image)  # Create 3D mesh
    save_mesh(mesh, args.output_file)  # Save 3D mesh
    visualize_mesh(mesh, marching_cubes)  # Visualize 3D mesh
