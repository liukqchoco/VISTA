import os
from os.path import join as p_join

import yaml


class Config:
  def __init__(self):
    # setting CNN (graphic elements) model
    self.ROOT_IMG_COMPONENT = None
    self.ROOT_MERGE = None
    self.ROOT_OCR = None
    self.ROOT_IP = None
    self.ROOT_IMG_ORG = None
    self.ROOT_INPUT = None
    self.ROOT_OUTPUT = None
    self.image_shape = (64, 64, 3)
    self.element_class = [
      'Button', 'CheckBox', 'Chronometer', 'EditText', 'ImageButton', 'ImageView',
      'ProgressBar', 'RadioButton', 'RatingBar', 'SeekBar', 'Spinner', 'Switch',
      'ToggleButton', 'VideoView', 'TextView'
    ]
    self.class_number = len(self.element_class)

    self.COLOR = {
      'Button': (0, 255, 0), 'CheckBox': (0, 0, 255), 'Chronometer': (255, 166, 166),
      'EditText': (255, 166, 0), 'ImageButton': (77, 77, 255), 'ImageView': (255, 0, 166),
      'ProgressBar': (166, 0, 255), 'RadioButton': (166, 166, 166), 'RatingBar': (0, 166, 255),
      'SeekBar': (0, 166, 10), 'Spinner': (50, 21, 255), 'Switch': (80, 166, 66),
      'ToggleButton': (0, 66, 80), 'VideoView': (88, 66, 0), 'TextView': (169, 255, 0),
      'NonText': (0, 0, 255), 'Compo': (0, 0, 255), 'Text': (169, 255, 0), 'Block': (80, 166, 66)
    }

  def build_output_folders(self):
    # setting data flow paths
    with open('config/application.yml', 'r') as f:
      config = yaml.safe_load(f)['test']
    self.ROOT_INPUT = config['root_input']
    self.ROOT_OUTPUT = config['root_output']

    self.ROOT_IMG_ORG = p_join(self.ROOT_INPUT, "org")
    self.ROOT_IP = p_join(self.ROOT_OUTPUT, "ip")
    self.ROOT_OCR = p_join(self.ROOT_OUTPUT, "ocr")
    self.ROOT_MERGE = p_join(self.ROOT_OUTPUT, "merge")
    self.ROOT_IMG_COMPONENT = p_join(self.ROOT_OUTPUT, "components")
    if not os.path.exists(self.ROOT_IP):
      os.mkdir(self.ROOT_IP)
    if not os.path.exists(self.ROOT_OCR):
      os.mkdir(self.ROOT_OCR)
    if not os.path.exists(self.ROOT_MERGE):
      os.mkdir(self.ROOT_MERGE)
