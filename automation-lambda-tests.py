from subprocess import call
import yaml

with open("automation-config.yaml", 'r') as ymlconfig:
    config = yaml.load(ymlconfig)

stackTestLambdas = config['StackTestLambdaArns']
templateTestLambdas = config['TemplateTestLambdaArns']

#TODO: for each ARN, execute a lambda (sync) and throw an exception if any of them fail (halting the build / deploy)
