# -*- coding: utf-8 -*-
__title__ = "Place Elements Along Curve"                           # Name of the button displayed in Revit UI
__doc__ = """Version = 1.0
Date    = 12.06.2022
_____________________________________________________________________
Description:
This tool will place selected FamilyType along selected ModelLine/ModelSpline.

_____________________________________________________________________
How-to:
-> Click on the button
-> Select ModelLine
-> Select Point-Based FamilyInstance
_____________________________________________________________________""" # Button Description shown in Revit UI

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
# ==================================================
from Autodesk.Revit.DB import *                                         # Import everything from DB (Very good for beginners)
# pyRevit
from pyrevit import revit, forms                                        # import pyRevit modules. (Lots of useful features)

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
# ==================================================
doc     = __revit__.ActiveUIDocument.Document   # Document   class from RevitAPI that represents project. Used to Create, Delete, Modify and Query elements from the project.
uidoc   = __revit__.ActiveUIDocument          # UIDocument class from RevitAPI that represents Revit project opened in the Revit UI.
app     = __revit__.Application                 # Represents the Autodesk Revit Application, providing access to documents, options and other application wide data and settings.



def convert_m_to_internal(length):
    """Function to convert m to internal Revit units(feet)."""
    rvt_year = int(app.VersionNumber)

    # RVT >= 2022
    if rvt_year < 2022:
        from Autodesk.Revit.DB import DisplayUnitType
        return UnitUtils.Convert(length,
                                 DisplayUnitType.DUT_METERS,
                                 DisplayUnitType.DUT_DECIMAL_FEET)
    # RVT >= 2022
    else:
        from Autodesk.Revit.DB import UnitTypeId
        return UnitUtils.ConvertToInternalUnits(length, UnitTypeId.Meters)



# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
# ==================================================

# Select Model Line
from pyrevit import revit
with forms.WarningBar(title="Select Model Line:", handle_esc=True):
    selected_curve = revit.pick_element()
# ==================================================

# Check Type
element_type = type(selected_curve)
if element_type not in [ModelNurbSpline, ModelLine, ModelArc, ModelCurve, ModelEllipse]:
    from pyrevit import forms
    forms.alert('This tool needs a Model Line.', exitscript=True)
# ==================================================
# Select Family Type
with forms.WarningBar(title="Select Element that will be placed:", handle_esc=True):
    select_placing_element = revit.pick_element()
    try:
        pt = select_placing_element.Location.Point
    except:
        forms.alert('FamilyInstance has to be Point Based. Please try again.', exitscript=True)

# ==================================================

# Distance + convert
step = convert_m_to_internal(0.5)

# ==================================================

# Convert to Curve
geo_curve = selected_curve.GeometryCurve
# ==================================================


# Get points on curve (C# EXAMPLE)
# link: https://thebuildingcoder.typepad.com/blog/2013/11/placing-equidistant-points-along-a-curve.html
# C_sharp_example = """
#   double param1 = curve.GetEndParameter(0);
#   double param2 = curve.GetEndParameter(1);
#
#   double paramCalc = param1 + ((param2 - param1)
#     * requiredDist / curveLength);
#
#   XYZ evaluatedPoint = null;
#
#   if (curve.IsInside(paramCalc))
#   {
#     double normParam = curve
#       .ComputeNormalizedParameter(paramCalc);
#
#     evaluatedPoint = curve.Evaluate(
#       normParam, true)));} """
# ==================================================

# Generate points along curve
pt_0 = geo_curve.GetEndParameter(0)
pt_1 = geo_curve.GetEndParameter(1)

list_XYZ = []
n=1
while True:
    dist = step * n
    n+=1
    if dist > geo_curve.Length:
        break

    # Get point on curve
    paramCalc = pt_0 + ((pt_1 - pt_0) * dist / geo_curve.Length)
    if geo_curve.IsInside(paramCalc):
        normParam = geo_curve.ComputeNormalizedParameter(paramCalc)
        evaluatedPoint = geo_curve.Evaluate(normParam, True)

        # add point to the list
        list_XYZ.append(evaluatedPoint)


# ==================================================
# Place family
t = Transaction(doc, 'Placing Elements on Curve')
t.Start()

for pt in list_XYZ:
    from Autodesk.Revit.DB.Structure import StructuralType
    doc.Create.NewFamilyInstance(pt, select_placing_element.Symbol, StructuralType.NonStructural)

# change here
t.Commit()