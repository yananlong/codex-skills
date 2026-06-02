from .onnx.BoxRFDGNN import BoxRFDGNN

# RF2.4.1 model version
__version__ = '260225'

def get_model(model_name='BoxRFDGNN', feature_set_name='imf+rf',
              input_type='text',
              config_path=None, model_path=None, imf_model_path=None):

    input_type = tuple(input_type.split('+'))
    if model_name == 'BoxRFDGNN':
        return BoxRFDGNN(config_path, model_path, imf_model_path, input_type=input_type,
                         feature_set_name=feature_set_name)
    else:
        raise Exception(f'Invalid model name = {model_name}')
