from args import args
import torchvision
import json
import os
from torchvision import transforms, datasets
import torch 

# Read Graph for imagenet names and classes
with open(os.path.join('datasets', 'ilsvrc_2012_dataset_spec.json'), 'r') as file:
    graph = json.load(file)

imagenet_class_names = {}
for subset in graph['split_subgraphs'].values():
    for entity in subset:
        if len(entity['children_ids']) == 0:
            imagenet_class_names[entity['wn_id']] = entity['words']

all_results = {}

### generate data for miniimagenet
for dataset in ["train","validation","test"]:
    firstLine = True
    classToIdx = {}
    nClass = 0
    result = {"data":[], "targets":[], "name":"miniimagenet_" + dataset, "num_classes":0, "name_classes":[]}
    with open(args.dataset_path + "miniimagenetimages/" + dataset + ".csv") as f:
        for row in f:
            if firstLine:
                firstLine = False
            else:
                fileName, classIdx = row.split(",")
                classIdx = classIdx.split("\n")[0]
                if classIdx in classToIdx.keys():
                    result["data"].append("miniimagenetimages/images/" + fileName)
                    result["targets"].append(classToIdx[classIdx])
                else:
                    classToIdx[classIdx] = nClass
                    result["data"].append("miniimagenetimages/images/" + fileName)
                    result["targets"].append(nClass)
                    result["name_classes"].append(imagenet_class_names[classIdx])
                    nClass += 1
    result["num_classes"] = nClass
    result["num_elements_per_class"] = [600]*nClass
    
    all_results["miniimagenet_" + dataset] = result
    print("Done for miniimagenet_" + dataset + " with " + str(nClass) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")

### generate data for tieredimagenet
for dataset,folderName in [("train","train"),("validation","val"),("test","test")]:
    directories = os.listdir(args.dataset_path + "tieredimagenet/" + folderName)
    result = {"data":[], "targets":[], "name":"tieredimagenet_" + dataset, "num_classes":0, "name_classes":[]}
    for i,classIdx in enumerate(directories):
        num_elements_per_class = 0
        for fileName in os.listdir(args.dataset_path + "tieredimagenet/" + folderName + "/" + classIdx):
            result["data"].append("tieredimagenet/" + folderName + "/" + classIdx + "/" + fileName)
            result["targets"].append(i)
            num_elements_per_class += 1
        result["num_elements_per_class"] = num_elements_per_class
        result["name_classes"].append(imagenet_class_names[classIdx])
        
    result["num_classes"] = i + 1
    all_results["tieredimagenet_" + dataset] = result
    print("Done for tieredimagenet_" + dataset + " with " + str(i+1) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")

### generate data for cifarfs
for dataset,folderName in [("train","meta-train"),("validation","meta-val"),("test","meta-test")]:
    directories = os.listdir(args.dataset_path + "cifar_fs/" + folderName)
    result = {"data":[], "targets":[], "name":"cifarfs_" + dataset, "num_classes":0, "name_classes":[]}
    for i,classIdx in enumerate(directories):
        num_elements_per_class = 0
        for fileName in os.listdir(args.dataset_path + "cifar_fs/" + folderName + "/" + classIdx):
            result["data"].append("cifar_fs/" + folderName + "/" + classIdx + "/" + fileName)
            result["targets"].append(i)
        num_elements_per_class += 1
        result["num_elements_per_class"] = num_elements_per_class
        result["name_classes"].append(classIdx)

    result["num_classes"] = i + 1
    all_results["cifarfs_" + dataset] = result
    print("Done for cifarfs_" + dataset + " with " + str(i+1) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")


## generate data for mnist
for dataset in ['train', 'test']:
    result = {"data":[], "targets":[], "name":"mnist_" + dataset, "num_classes":0, "name_classes":[], "num_elements_per_class": []}

    pytorchDataset = datasets.MNIST(args.dataset_path, train = dataset != "test", download = False)
    targets = pytorchDataset.targets
    for c in range(targets.max()):
        result["num_elements_per_class"].append(len(torch.where(targets==c)[0]))
    result["num_classes"] = len(result["num_elements_per_class"])+1
    all_results['mnist_'+ dataset] = result
    print("Done for mnist_" + dataset + " with " + str(i+1) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")

### generate data for imagenet metadatasets
# Parse Graph 
class_folders = {k:[p['wn_id'] for p in graph['split_subgraphs'][k] if len(p['children_ids']) == 0] for k in ['TRAIN', 'TEST', 'VALID']} # Existing classes    
# Get duplicates from other datasets which should be removed from ImageNet
duplicates = []
duplicate_files =  ['ImageNet_CUBirds_duplicates.txt', 'ImageNet_Caltech101_duplicates.txt', 'ImageNet_Caltech256_duplicates.txt']
for file in duplicate_files:
    with open(os.path.join('datasets', file), 'r') as f:
        duplicates_tmp = f.read().split('\n')
    duplicates += [p.split('#')[0].replace(' ','') for p in duplicates_tmp if len(p)>0 and p[0] not in ['#']] # parse the duplicates files

path = os.path.join('metadatasets', 'ILSVRC2012_img_train')
for dataset, folderName in [('train', 'TRAIN'), ('test', 'TEST'), ('validation','VALID')]:
    result = {"data":[], "targets":[], "name":"metadataset_imagenet_" + dataset, "num_classes":0, "name_classes":[], "num_elements_per_class":[], "classIdx":{}}
    for i, classIdx in enumerate(class_folders[folderName]):
        num_elements_per_class = 0
        for fileName in os.listdir(os.path.join(args.dataset_path, path, classIdx)):
            if os.path.join(classIdx, fileName) not in duplicates:
                result["data"].append(os.path.join(path, classIdx, fileName))
                result["targets"].append(i)
                num_elements_per_class +=1
        result["name_classes"].append(imagenet_class_names[classIdx])
        result["classIdx"][classIdx] = i
        result["num_elements_per_class"].append(num_elements_per_class)

    result["num_classes"] = i + 1   
    all_results["metadataset_imagenet_" + dataset] = result
    print("Done for metadataset_imagenet_" + dataset + " with " + str(i+1) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")


def split_fn(json_path):
    with open(args.dataset_path+json_path) as jsonFile:
        split = json.load(jsonFile)
        jsonFile.close()
    return split



def get_data(jsonpath, image_dir):
    split = split_fn(jsonpath)
    data ,num_classes, num_elts = {},{},{}
    split = {"validation" if k == 'valid' else k:v for k,v in split.items()}
    for index_subset, subset in enumerate(split.keys()):
        data[subset] = {'data': [], 'target' : [] , 'name_classes' : []}
        num_elts[subset] = []
        l_classes = split[subset]
        num_classes[subset] = len(l_classes)
        for index_class, cl in enumerate(l_classes):
            cl_path = args.dataset_path + image_dir + cl
            images = sorted(os.listdir(cl_path))                    #Careful here you might mix the order (not sure that sorted is good enough)
            for index_image , im in enumerate(images):
                data[subset]['data'].append(cl_path + im)
                data[subset]['target'].append(index_class)
                num_elts[subset].append([cl, index_image+1])
            data[subset]['name_classes'].append(cl)
        data[subset]['num_classes'] = index_class+1
    return data, num_elts

##### generate data for CUB and DTD
result_cub, nb_elts_cub = get_data("metadatasets/CUB_200_2011/cu_birds_splits.json", "metadatasets/CUB_200_2011/images/")
results_dtd , nb_elts_dtd = get_data('metadatasets/dtd/dtd_splits.json', 'metadatasets/dtd/images/')
for dataset in ['train', 'test', 'validation']:
    all_results["metadataset_cub_" + dataset] = result_cub[dataset]
    print("Done for metadataset_cub_" + dataset + " with " + str(result_cub[dataset]['num_classes']) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")
    all_results["metadataset_dtd_" + dataset] = results_dtd[dataset]
    print("Done for metadataset_dtd_" + dataset + " with " + str(results_dtd[dataset]['num_classes']) + " classes and " + str(len(result["data"])) + " samples (" + str(len(result["targets"])) + ")")

f = open(args.dataset_path + "datasets.json", "w")
f.write(json.dumps(all_results))
f.close()
