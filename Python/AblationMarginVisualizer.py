import os
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# AblationMarginVisualizer
#

class AblationMarginVisualizer:
  def __init__(self, parent):
    parent.title = "AblationMarginVisualizer"
    parent.categories = ["IGT"]
    parent.dependencies = []
    parent.contributors = ["Junichi Tokuda (BWH)"]
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This module was supported by National Center for Image Guided Therapy and NIH R01CA138586.
    """
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['AblationMarginVisualizer'] = self.runTest

  def runTest(self):
    tester = AblationMarginVisualizerTest()
    tester.runTest()

#
# qAblationMarginVisualizerWidget
#
class AblationMarginVisualizerWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):

    # Instantiate and connect widgets ...
    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "AblationMarginVisualizer Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    #
    # Basic Area
    #
    basicCollapsibleButton = ctk.ctkCollapsibleButton()
    basicCollapsibleButton.text = "Basic"
    self.layout.addWidget(basicCollapsibleButton)

    # Layout within the dummy collapsible button
    basicFormLayout = qt.QFormLayout(basicCollapsibleButton)

    #
    # Tumor label selector
    #
    self.tumorLabelSelector = slicer.qMRMLNodeComboBox()
    self.tumorLabelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.tumorLabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.tumorLabelSelector.selectNodeUponCreation = True
    self.tumorLabelSelector.addEnabled = False
    self.tumorLabelSelector.removeEnabled = False
    self.tumorLabelSelector.noneEnabled = False
    self.tumorLabelSelector.showHidden = False
    self.tumorLabelSelector.showChildNodeTypes = False
    self.tumorLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.tumorLabelSelector.setToolTip( "Select label image of the tumor volume" )
    basicFormLayout.addRow("Tumor Volume: ", self.tumorLabelSelector)

    self.outputModelSelector = slicer.qMRMLNodeComboBox()
    self.outputModelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.outputModelSelector.selectNodeUponCreation = False
    self.outputModelSelector.addEnabled = False
    self.outputModelSelector.renameEnabled = False
    self.outputModelSelector.removeEnabled = False
    self.outputModelSelector.noneEnabled = False
    self.outputModelSelector.showHidden = False
    self.outputModelSelector.showChildNodeTypes = False
    self.outputModelSelector.setMRMLScene( slicer.mrmlScene )
    self.outputModelSelector.setToolTip( "Select a surface model of the ablation volume" )
    basicFormLayout.addRow("Ablation Volume Model: ", self.outputModelSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    basicFormLayout.addRow(self.applyButton)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    #
    # Visualization Area
    #
    visualizationCollapsibleButton = ctk.ctkCollapsibleButton()
    visualizationCollapsibleButton.text = "Visualization"
    self.layout.addWidget(visualizationCollapsibleButton)

    # Layout within the dummy collapsible button
    visualizationFormLayout = qt.QFormLayout(visualizationCollapsibleButton)

    self.colorMapSelector = slicer.qMRMLColorTableComboBox()
    self.colorMapSelector.setMRMLScene( slicer.mrmlScene )
    visualizationFormLayout.addRow("Color Table: ", self.colorMapSelector)

    self.colorMapSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onColorTableSelect)

    #self.colorRangeWidget = slicer.qMRMLRangeWidget()
    self.colorRangeWidget = ctk.ctkRangeWidget()
    self.colorRangeWidget.setToolTip("Set color range")
    visualizationFormLayout.addRow("Color Range: ", self.colorRangeWidget)
    self.colorRangeWidget.connect('valuesChanged(double, double)', self.updateColorRange)

    self.showScaleButton = qt.QCheckBox()
    self.showScaleButton.setText('Show Scale')
    self.showScaleButton.checked = False
    self.showScaleButton.setToolTip('Check to show the scale bar in the 3D viewer')
    visualizationFormLayout.addRow("Ablation Volume Model: ", self.showScaleButton)

    self.showScaleButton.connect('clicked(bool)', self.onShowScaleButton)

    # connections
    #self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    #self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    ## Create a scale
    self.scalarBarWidget = vtk.vtkScalarBarWidget()
    actor = self.scalarBarWidget.GetScalarBarActor()
    actor.SetOrientationToVertical()
    actor.SetNumberOfLabels(11)
    actor.SetTitle("")
    actor.SetLabelFormat(" %#8.3f")
    actor.SetPosition(0.1, 0.1)
    actor.SetWidth(0.1)
    actor.SetHeight(0.8)
    self.scalarBarWidget.SetEnabled(0)    

    layout = slicer.app.layoutManager()
    view = layout.threeDWidget(0).threeDView()
    renderer = layout.activeThreeDRenderer()
    self.scalarBarWidget.SetInteractor(renderer.GetRenderWindow().GetInteractor())


  def onApplyButton(self):
    logic = AblationMarginVisualizerLogic()
    #logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode())
    ## Invoke the distance map generation and surface map probing process
    self.generateDistanceMap()

  def onColorTableSelect(self):
    self.adjustScalarBar()
    self.forceRender()

  def updateColorRange(self, min, max):
    probeModel = self.outputModelSelector.currentNode()
    if probeModel:
      dnode = probeModel.GetDisplayNode()
      dnode.SetScalarRange(min, max)
      self.adjustScalarBar()

  def generateDistanceMap(self):
    print("Generating distance map.")
    ## Create an scalar volume node for distance map
    self.distanceMapNode = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(self.distanceMapNode)

    ## Call CLI
    parameters = {}
    parameters["inputVolume"] = self.tumorLabelSelector.currentNode().GetID()
    parameters["outputVolume"] = self.distanceMapNode.GetID()
    parameters["physicalDistance"] = True
    distanceMap = slicer.modules.distancemap
    cliNode = slicer.cli.run(distanceMap, None, parameters)
    cliNode.AddObserver('ModifiedEvent', self.probeDistanceMap)
    
  def probeDistanceMap(self, caller, status):
    if (caller.GetStatus() == slicer.vtkMRMLCommandLineModuleNode.Completed):
      print("Probing distance map.")
      parameters = {}
      probeModel = self.outputModelSelector.currentNode()
      parameters["InputVolume"] = self.distanceMapNode.GetID()
      parameters["InputModel"] = probeModel.GetID()
      parameters["OutputModel"] = probeModel.GetID()
      probe = slicer.modules.probevolumewithmodel
      cliNode = slicer.cli.run(probe, None, parameters)
      cliNode.AddObserver('ModifiedEvent', self.postSetting)

  def postSetting(self, caller, status):
    if (caller.GetStatus() == slicer.vtkMRMLCommandLineModuleNode.Completed or
        caller.GetStatus() == slicer.vtkMRMLCommandLineModuleNode.Idle):
      print("Setting surface model.")

      probeModel = self.outputModelSelector.currentNode()
      dnode = probeModel.GetDisplayNode()
      dnode.SetAutoScalarRange(0)   ## Turn off auto scalar range
      dnode.SetActiveScalarName('NRRDImage')
      dnode.SetScalarVisibility(1)
      slicer.mrmlScene.RemoveNode(self.distanceMapNode)
      self.distanceMapNode = None

      self.adjustScalarBar()
      self.forceRender()

      
  def onShowScaleButton(self):
    logic = AblationMarginVisualizerLogic()
    if self.showScaleButton.checked:
      self.enableScalarBar(1)
    else:
      self.enableScalarBar(0)
      
  def enableScalarBar(self, s):
    self.scalarBarWidget.SetEnabled(s)
    if s:
      self.adjustScalarBar()
    self.forceRender()

  def adjustScalarBar(self):
    probeModel = self.outputModelSelector.currentNode()
    if probeModel:
      dnode = probeModel.GetDisplayNode()
      r = dnode.GetScalarRange()
      self.colorRangeWidget.setValues(r[0], r[1])

      colorNode = self.colorMapSelector.currentNode()
      if colorNode: 
        colorNode.GetLookupTable().SetRange(r[0], r[1])
        dnode.SetAndObserveColorNodeID(colorNode.GetID())
        self.scalarBarWidget.GetScalarBarActor().SetLookupTable(colorNode.GetLookupTable())
        self.scalarBarWidget.GetScalarBarActor().Modified()

  def forceRender(self):
    layout = slicer.app.layoutManager()
    renderer = layout.activeThreeDRenderer()
    rwindow = renderer.GetRenderWindow()
    rwindow.Render()

  def onReload(self,moduleName="AblationMarginVisualizer"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)
    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()


#
# AblationMarginVisualizerLogic
#
class AblationMarginVisualizerLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that 
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def run(self,inputVolume,outputVolume):
    """
    Run the actual algorithm
    """
    return True


class AblationMarginVisualizerTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_AblationMarginVisualizer1()

  def test_AblationMarginVisualizer1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = AblationMarginVisualizerLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
