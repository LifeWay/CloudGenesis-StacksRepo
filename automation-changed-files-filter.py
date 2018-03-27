import os
import shutil
from git import Repo

dir_path = os.path.dirname(os.path.realpath(__file__))
repo = Repo(dir_path)
os.makedirs("templates-sync/templates", exist_ok=True)
os.makedirs("stacks-sync/stacks", exist_ok=True)

# Get the head commit + the prev commit
a_commit = repo.commit('HEAD')
b_commit = repo.commit('HEAD~1')

print ("Diffing commit:", a_commit, "to:", b_commit, " for the set of files we need to eval")

def createChangeSets(items, basePath, deletedFile):
    for item in items:
        if(item.deleted_file):
            print("To Delete: " + item.a_path)
            deletedFile.write(item.a_path + '\n')
        elif(item.renamed_file):
            print("To Delete (Renamed): " + item.a_path)
            deletedFile.write(item.a_path + '\n')
            print("To Create (Renamed): " + item.b_path)
        else:
            print("To Create / Update: " + item.a_path)
            filePath = basePath + "/" + item.a_path
            os.makedirs(os.path.dirname(filePath), exist_ok=True)
            shutil.copy2(item.a_path, filePath)

#Get set of changes - only applies to stacks and templates.
stacks = list(filter(lambda x: x.a_path.startswith("stacks/"), b_commit.diff(a_commit)))
templates = list(filter(lambda x: x.a_path.startswith("templates/"), b_commit.diff(a_commit)))

deleteTemplates = open('templates-to-delete.txt', 'w')
deleteStacks = open('stacks-to-delete.txt', 'w')

createChangeSets(templates, "templates-sync", deleteTemplates)
createChangeSets(stacks, "stacks-sync", deleteStacks)

deleteTemplates.close
deleteStacks.close
