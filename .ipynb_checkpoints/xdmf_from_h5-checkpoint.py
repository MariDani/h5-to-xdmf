import importlib
import matplotlib.image as mpimg
import os
import re
import h5py
import platform
import numpy as np
import ipywidgets as widgets
from hdfviewer.widgets.HDFViewer import HDFViewerWidget
from hdfviewer.widgets.PathSelector import PathSelector
import matplotlib.pyplot as plt
from IPython.display import display
import h5Preview.h5Preview as h5Preview

importlib.reload(h5Preview)

# define global variables
dataset_type_w = widgets.RadioButtons()
dirname_w = widgets.Text()
xdmf_name_w = widgets.Text()
h5PreviewSelectedFile: PathSelector
existingXDMFParts = False
slash = "//"
if platform.system() == "Windows":
    slash = "\\"

style = {"description_width": "initial"}


def createConfirmButton(text):
    confirmButton = widgets.Button(description=text)
    buttonHtml = widgets.HTML("<br>")
    display(buttonHtml, confirmButton)
    return confirmButton


def init():
    global dataset_type_w
    global dirname_w
    global xdmf_name_w

    output = widgets.Output()

    dataset_type_w = widgets.RadioButtons(
        options=["particles", "fields"],
        description="Dataset type:",
        disabled=False,
        style=style
    )

    dirname_w = widgets.Text(
        value=f"D:{slash}Jupyter{slash}jupyter-xdmf-from-h5{slash}data{slash}3D_fields",
        description="Dirname:",
        disabled=False,
        style=style
    )

    xdmf_name_w = widgets.Text(
        value="fields",
        description="XDMF filename:",
        disabled=False,
        style=style
    )

    creation_option_w = widgets.Dropdown(
        options=["create XDMF parts", "load XDMF parts"],
        value="create XDMF parts",
        description="Creation option",
        disabled=False,
        style=style
    )

    datasetTitle = widgets.HTML("<h1>Dataset parameters</h1>")
    display(datasetTitle)

    display(dataset_type_w, dirname_w, xdmf_name_w, creation_option_w)

    confirmButton = createConfirmButton("Continue")

    @output.capture()
    def on_button_clicked(b):
        if creation_option_w.value == "create XDMF parts":
            createXDMFParts()
        else:
            loadXDMFParts()

    confirmButton.on_click(on_button_clicked)

    display(output)


def getDirname():
    return dirname_w.value


def getH5Keys():

    def getGroupKeys(group, keyItems, prev):
        for key in keyItems:
            if not isinstance(group.get(key), h5py.Dataset):
                newgroup = group.get(key)
                getGroupKeys(newgroup, newgroup.keys(), key)
            else:
                keys.append(f"{prev}/{key}" if prev else key)

    keys = []
    allfiles = sorted(os.listdir(dirname_w.value))
    for filename in allfiles:
        if filename.endswith(".h5"):
            f = h5py.File(f"{dirname_w.value}{slash}{filename}", "r")
            getGroupKeys(f, f.keys(), "")
            f.close()
            return keys


def createXDMFForAllFiles(header, body, footer, p):

    def getParticleCount(f):
        attrShape = ()
        for name, w in p["attributes_w"].items():
            if w.value:
                shape = f.get(name).shape
                if attrShape:
                    if attrShape != shape:
                        print(
                            "Warning: Selected attributes have differenet particle count")
                else:
                    attrShape = shape
        return attrShape

    def writeXDMF(xdmf):
        if os.path.isfile(f"{dirname_w.value}{slash}{xdmf_name_w.value}.xdmf"):
            os.unlink(f"{dirname_w.value}{slash}{xdmf_name_w.value}.xdmf")

        fout = open(f"{dirname_w.value}{slash}{xdmf_name_w.value}.xdmf", "w")
        fout.write(xdmf)
        fout.close()
        print(f"Done writing {xdmf_name_w.value}.xdmf")

    def writeXDMFParts(parts):
        for name, part in parts.items():
            if os.path.isfile(f"{dirname_w.value}{slash}{xdmf_name_w.value}-{name}.txt"):
                os.unlink(f"{dirname_w.value}{slash}{xdmf_name_w.value}-{name}.txt")

            fout = open(
                f"{dirname_w.value}{slash}{xdmf_name_w.value}-{name}.txt", "w")
            fout.write(part)
            fout.close()
            print(f"Done writing {xdmf_name_w.value}-{name}.txt")

    global existingXDMFParts
    output = header
    allfiles = sorted(os.listdir(dirname_w.value))

    for filename in allfiles:
        if filename.endswith(".h5"):
            f = h5py.File(f"{dirname_w.value}{slash}{filename}", "r")

            if dataset_type_w.value == "particles":
                shape_values = ()
                if existingXDMFParts:
                    shape_values = f[p["particles_col_count_w"].value].shape
                else:
                    shape_values = getParticleCount(f)
                if (len(shape_values) > 1 and shape_values[1] > shape_values[0]):
                    npart = shape_values[1]
                else:
                    npart = shape_values[0]
            else:
                npart = 0

            # realtime value is based on the last number in .h5 filename
            filename_nums = re.findall(r"\d+", filename[:-1])
            realtime = int(filename_nums[len(filename_nums)-1])
            section = body.replace("%TIME%", str(realtime))
            section = section.replace("%NPART%", str(npart))
            section = section.replace("%FILE%", filename)
            output += section
            f.close()
    output += footer

    writeXDMF(output)
    if not existingXDMFParts:
        writeXDMFParts({"header": header, "body": body, "footer": footer})


def createXDMFParts():

    def createAttributeWidget(h5Keys):
        attributes_w = {}

        for key in h5Keys:
            if key:
                attribute = widgets.Checkbox(
                    value=False,
                    description=f"{key}",
                    disabled=False,
                    style=style
                )
                attributes_w[key] = attribute

        return attributes_w

    def getAttributes(attributes_w):
        attributes = []
        for name, w in attributes_w.items():
            if w.value:
                attributes.append(name)
        return attributes

    def displayWidgetParamHtml(title, geometry, attr_w):
        title = widgets.HTML(f"<h2>{title}</h2>")
        display(title)

        axisHtml = widgets.HTML(
            "<h3>Axis</h3><p>Choose fields with axis data. For 2D data leave the <i>Z</i> axis field empty</p>")
        display(axisHtml)

        display(widgets.VBox(geometry))

        attrHtml = widgets.HTML(
            "<h3>Attributes</h3><p>Check those attributes which you would like to include in your <i>.xdmf</i> file. <strong>At least one</strong> attribute must be selected")
        display(attrHtml)
        for name, w in attr_w.items():
            display(w)

    def getParticlesParameters():

        h5Keys = getH5Keys()
        h5Keys.append("")

        particles_geometry_x_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[0],
            description="X:",
            disabled=False,
            style=style
        )

        particles_geometry_y_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[0],
            description="Y:",
            disabled=False,
            style=style
        )

        particles_geometry_z_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[-1],
            description="Z:",
            disabled=False,
            style=style
        )

        attributes_w = createAttributeWidget(h5Keys)
        displayWidgetParamHtml("Particle parameters", [particles_geometry_x_w,
                                                       particles_geometry_y_w, particles_geometry_z_w], attributes_w)

        return {
            "particles_geometry_x_w": particles_geometry_x_w,
            "particles_geometry_y_w": particles_geometry_y_w,
            "particles_geometry_z_w": particles_geometry_z_w,
            "attributes_w": attributes_w
        }

    def getFieldParameters():
        h5Keys = getH5Keys()
        h5Keys.append("")

        field_axis_x_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[0],
            description="X:",
            disabled=False,
            style=style
        )

        field_axis_y_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[0],
            description="Y:",
            disabled=False,
            style=style
        )

        field_axis_z_w = widgets.Dropdown(
            options=h5Keys,
            value=h5Keys[-1],
            description="Z:",
            disabled=False,
            style=style
        )

        attributes_w = createAttributeWidget(h5Keys)

        displayWidgetParamHtml("Field parameters", [field_axis_x_w,
                                                    field_axis_y_w, field_axis_z_w], attributes_w)

        return {
            "field_axis_x_w": field_axis_x_w,
            "field_axis_y_w": field_axis_y_w,
            "field_axis_z_w": field_axis_z_w,
            "attributes_w": attributes_w
        }

    def getFieldDimension(p):
        return "ZYX" if p["field_axis_z_w"].value else "YX"

    def getFieldXDMFHeader(p):
        def getDimensions(p):
            allfiles = sorted(os.listdir(dirname_w.value))
            for filename in allfiles:
                if filename.endswith(".h5"):
                    f = h5py.File(dirname_w.value + slash + filename, "r")

                    attrShape = ()
                    for name, w in p["attributes_w"].items():
                        if w.value:
                            shape = f.get(name).shape
                            if attrShape:
                                if attrShape != shape:
                                    print(
                                        "Warning: Selected attributes have differenet dimensions")
                                    attrShape = (0, 0, 0)
                                    break
                            else:
                                attrShape = shape

                    if len(attrShape) <= 2:
                        attrShape = (1, attrShape[0], attrShape[1])

                    return {
                        "x": attrShape[2],
                        "y": attrShape[1],
                        "z": attrShape[0]
                    }

        def getDimScale(dim, p):
            dimScale = {}

            allfiles = sorted(os.listdir(dirname_w.value))
            for filename in allfiles:
                if filename.endswith(".h5"):
                    f = h5py.File(dirname_w.value + slash + filename, "r")

                    xAxis = np.array(f.get(p["field_axis_x_w"].value))
                    dimScale["x"] = round(
                        (np.max(xAxis) - np.min(xAxis))/float(dim["x"]), 4)

                    yAxis = np.array(f.get(p["field_axis_y_w"].value))
                    dimScale["y"] = round(
                        (np.max(yAxis) - np.min(yAxis))/float(dim["y"]), 4)

                    if p["field_axis_z_w"].value:
                        zAxis = np.array(f.get(p["field_axis_z_w"].value))
                        dimScale["z"] = round(
                            (np.max(zAxis) - np.min(zAxis))/float(dim["z"]), 4)
                    else:
                        dimScale["z"] = 1

                    return dimScale

        dim = getDimensions(p)
        dimScale = getDimScale(dim, p)

        xdmf_header = f"""<?xml version="1.0" ?>
        <!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" [
            <!ENTITY c{getFieldDimension(p)} "{dim["z"]} {dim["y"]} {dim["x"]}">
            <!ENTITY cDX "{dimScale["z"]} {dimScale["y"]} {dimScale["x"]}">
        ]>
        <Xdmf Version="2.0">
        <Domain>
        <Grid Name="Time" GridType="Collection" CollectionType="Temporal">"""

        return xdmf_header

    def getFieldXDMFBody(p):

        def getLowerLeftCoord():
            lowerLeftCoord = {}
            # TO DO: now it works only for static textures
            allfiles = sorted(os.listdir(dirname_w.value))
            for filename in allfiles:
                if filename.endswith(".h5"):
                    f = h5py.File(dirname_w.value + slash + filename, "r")
                    lowerLeftCoord["x"] = np.min(
                        np.array(f.get(p["field_axis_x_w"].value)))
                    lowerLeftCoord["y"] = np.min(
                        np.array(f.get(p["field_axis_y_w"].value)))
                    if p["field_axis_z_w"].value:
                        lowerLeftCoord["z"] = np.min(
                            np.array(f.get(p["field_axis_z_w"].value)))
                    else:
                        lowerLeftCoord["z"] = 0
                    return lowerLeftCoord

        lowerLeftCoord = getLowerLeftCoord()

        xdmf_body = f"""
        <Grid Name="{xdmf_name_w.value}">
            <Time Value="%TIME%" />
            <Topology TopologyType="3DCoRectMesh" Dimensions="&c{getFieldDimension(p)};"/>
            <Geometry GeometryType="ORIGIN_DXDYDZ">
                <DataItem Format="XML" Dimensions="3">
                    {lowerLeftCoord["z"]} {lowerLeftCoord["y"]} {lowerLeftCoord["x"]}
                </DataItem>
                <DataItem Format="XML" Dimensions="3">&cDX;</DataItem>
            </Geometry>"""

        # add attributes
        for key in getAttributes(p["attributes_w"]):
            xdmf_body += f"""
            <Attribute Name="{key}" Center="Node" AttributeType="Scalar">
                <DataItem ItemType="Uniform" Format="HDF" NumberType="Float" Precision="8" Dimensions="&c{getFieldDimension(p)};">%FILE%:{key}
                </DataItem>
            </Attribute>"""

        xdmf_body += """
        </Grid>"""

        return xdmf_body

    def getParticleXDMFHeader():
        return """<?xml version="1.0" ?>
        <!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" [
        ]>
        <Xdmf Version="2.0">
        <Domain>
        <Grid Name="Time" GridType="Collection" CollectionType="Temporal">"""

    def getParticleXDMFBody(p):
        xdmf_body = f"""
        <Grid Name="{xdmf_name_w.value}">
            <Time Value="%TIME%" />
            <Topology TopologyType="Polyvertex" NumberOfElements="%NPART%" NodesPerElement="1" />"""

        # add geometry type
        if p["particles_geometry_z_w"].value:

            xdmf_body += f"""
            <Geometry GeometryType="X_Y_Z">
                <DataItem Name="X" ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART% 1" Format="HDF">
                    %FILE%:{p["particles_geometry_x_w"].value}
                </DataItem>
                <DataItem Name="Y" ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART% 1" Format="HDF">
                    %FILE%:{p["particles_geometry_y_w"].value}
                </DataItem>        
                <DataItem Name="Z" ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART% 1" Format="HDF">
                    %FILE%:{p["particles_geometry_z_w"].value}
                </DataItem>        
            </Geometry>"""

        else:
            xdmf_body += f"""
            <Geometry GeometryType="X_Y">
                <DataItem Name="X" ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART% 1" Format="HDF">
                    %FILE%:{p["particles_geometry_x_w"].value}
                </DataItem>
                <DataItem Name="Y" ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART% 1" Format="HDF">
                    %FILE%:{p["particles_geometry_y_w"].value}
                </DataItem>
            </Geometry>"""

            # add attributes
        for key in getAttributes(p["attributes_w"]):
            xdmf_body += f"""
            <Attribute Name="{key}" AttributeType="Scalar" Center="Node">
                <DataItem ItemType="Uniform" DataType="Float" Precision="4" Dimensions="%NPART%" Format="HDF">
                    %FILE%:{key}
                </DataItem>
            </Attribute>"""

        xdmf_body += """
        </Grid>"""

        return xdmf_body

    def getXDMFFooter():
        return """
        </Grid>

        </Domain>
        </Xdmf>"""

    output = widgets.Output()

    # fields
    if dataset_type_w.value == "fields":
        parameteres = getFieldParameters()
        confirmButton = createConfirmButton("Click to create .xdmf")

        @output.capture()
        def on_button_clicked(b):
            xdmf_header = getFieldXDMFHeader(parameteres)
            xdmf_body = getFieldXDMFBody(parameteres)
            createXDMFForAllFiles(xdmf_header, xdmf_body,
                                  getXDMFFooter(), parameteres)

        confirmButton.on_click(on_button_clicked)

    # particles
    else:
        parameteres = getParticlesParameters()
        confirmButton = createConfirmButton("Click to create .xdmf")

        @output.capture()
        def on_button_clicked(b):
            xdmf_header = getParticleXDMFHeader()
            xdmf_body = getParticleXDMFBody(parameteres)
            createXDMFForAllFiles(xdmf_header, xdmf_body,
                                  getXDMFFooter(), parameteres)

        confirmButton.on_click(on_button_clicked)

    display(output)


def loadXDMFParts():
    def loadData(data):
        f = open(data.path, "r")
        return(f.read())

    def getParticlesCount():
        if dataset_type_w.value == "particles":
            h5Keys = getH5Keys()
            h5Keys.append("")

            particles_col_count_w = widgets.Dropdown(
                options=h5Keys,
                value=h5Keys[0],
                description="Particles col count:",
                disabled=False,
                style=style
            )

            display(particles_col_count_w)

            return {"particles_col_count_w": particles_col_count_w}
        else:
            return {}

    output = widgets.Output()
    global existingXDMFParts
    existingXDMFParts = True

    parameters = getParticlesCount()

    headerPath = PathSelector(
        startingPath=dirname_w.value, extensions=[".txt"])
    print("Select header")
    display(headerPath.widget)
    bodyPath = PathSelector(startingPath=dirname_w.value, extensions=[".txt"])
    print("Select body")
    display(bodyPath.widget)
    footerPath = PathSelector(
        startingPath=dirname_w.value, extensions=[".txt"])
    print("Select footer")
    display(footerPath.widget)

    confirmButton = widgets.Button(description="OK")
    display(confirmButton)

    @output.capture()
    def on_button_clicked(b):
        createXDMFForAllFiles(loadData(headerPath), loadData(
            bodyPath), loadData(footerPath), parameters)

    confirmButton.on_click(on_button_clicked)

    display(output)
