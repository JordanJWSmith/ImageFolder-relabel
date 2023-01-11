# ImageFolder-relabel

An open source GUI to enable quick and simple relabelling for Pytorch's `ImageFolder` framework. 

## Pytorch ImageFolder

Pytorch's `ImageFolder` class provides a convenient dataloader for image datasets. 
By providing a root directory, `ImageFolder` infers the image labels based on the directory structure. 

For example, say we're building a [sausage-detector](https://github.com/JordanJWSmith/sausage-classifier). 
We use the following directory structure...

```
- input/
    - training_data/
        - sausage/
            - sausage_1.png
            - sausage_2.png
            - etc
        - non_sausage/
            - pizza_1.png
            - pasta_1.png
            - etc
    - validation_data/
        - sausage/
            - sausage_3.png
            - sausage_4.png
        - non_sausage/
            - pizza_2.png
            - pasta_2.png
            
```

We pass the `training_data` and `validation_data` directories to `ImageFolder`, 
and the corresponding image labels are inferred.

```
train_dataset = datasets.ImageFolder(
    root='input/training_data',
    transform=train_transform
)

valid_dataset = datasets.ImageFolder(
    root='input/validation_data',
    transform=valid_transform
)
```