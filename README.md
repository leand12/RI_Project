

# RI Project 

## Authors

Bruno Bastos\
Leandro Silva


## How to run

The indexer and tokinizer provide the user a range of different options to customize the way they work. Files can be runned providing the desired parameters via terminal or by using a configuration file.

### Indexer

The indexer has a few options:

--positional
```
    -p 
```
when provided, saves the terms' positions in a document. This increases the required RAM and disk space, but can give better results when searching for a phrase.

--load-zip
```

```
when provided, expects a zipped file to be passed as an argument. It will then unzip the file as it reads it. This decreases the amount of space required to store the file, since it is zipped, but the process of unzipping while reading it takes more time.

--save-zip
```

```
when provided, the output files of the indexer while be zipped. This saves disk space in exchange for a slower read whenever a user is making a query.

--rename-doc
```

```
when provided, the documents will be renamed as a integer which occupies less bytes to store. For smaller number of documents, this will decrease the space required to store the indexer, but in exchange, will consume a bit more space in RAM. For larger number of documents, it will not work, as it will end up needing more space to store a single document.


-file-location
```

```
with this flag activated, the location of a term in a file will be stored in memory and later send to disk. This will increase the speed at which the indexer accesses a certain term, but will need more disk storage and RAM. 


--file-location-step
```

```
the step corresponds to the number of terms that are skipped in order to save the next file position. A bigger step will result in a slower search but decreases the disk space required to save the positions. A step of 1 keeps the position for every term in the corresponding file.

--block-threshold
```

```
corresponds to the maximum number of documents that can be stored in a block. A smaller value will result in more files, slowing down the merge and takes more time writting to disk. While if a higher value is choosed, the indexer can run out of RAM.

--merge-threshold
```

```
corresponds to the maximum number of postings for a merged file in disk. The higher the value, lesser files will be created, but can slow down search as there are bigger files to look for the terms.

--block-dir
```

```
the temporary directory where the blocks will be stored. After the merge the blocks and this directory are deleted.

--merge-dir
```

```
the final directory where the indexer is stored. This directory should contain a ".metadata" directory containing the necessary metadata files required for the indexer to be loaded.


### Tokenizer

--case-folding
```

```
chooses whether or not to convert every token to lowercase.

--no-numbers
```

```
discards every token that is a number.


The tokenizer parameters will decide how the tokens are processed.

--stemmer
```

```
makes use of the Snowball stemmer for english words.

--min-length
```

```
only tokens with size greater or equal to the minimum length value are accounted.

--stopwords-file
```

```
discards every word that is contained in the stopwords file.

--contractions-file
```

```
uses a contraction file that has many english contractions. If a token matches one of the contractions it is converted in the non contracted list of tokens.
