

# RI Project 

## Authors

Bruno Bastos\
Leandro Silva


## How it works

There are 3 important files in this project: tokenizer.py, indexer.py and query.py.


### Tokenizer

The tokenizer is responsible for the processing of tokens in a document. Its main functionalities
are transforming the tokens into terms and pass thoes terms to the indexer together with the information of the document, such as id and position of the token.

There are multiple strategies that are being used here.
The tokenizer reads one document at a time and, after selecting the required fields, it splits the text word by word, where each word is splitted by a space.

With this list of tokens, it then normalizes each token, transforming it into a term.
Every token that has a non alphanumeric character, will have that character replace by a space, and then the tokens are splitted, forming more tokens.
The user can set the minimum length of a token and those that are smaller than that number will be discarded.
A stopword file containing the tokens that should be discarded can be provided by the user but it is not necessary.
There can also be provided a list of contractions, which is mostly used in english, that will transform contractions into the respective tokens.(ex: I've -> I have)
There is an option to remove every token that is a number, integer or float.
It is used casefolding to make each token lowercase and transform some letters into others.
Finally, the remaing tokens will go through the stemmer and the result will be a list of terms.

The list of terms is then given to the indexer with the positional information of the term and the document id.


### Indexer

The indexer makes use of the list of terms provided by the tokenizer and starts the indexing process.
Every term is stored in an hashtable(dict) together with the list of postings(list with the ids of the documents where the term appears). If the "positional" flag is set, instead of storing a list postings, it is stored for each term a dictionary with the document id and a respective list of positions where that term appears in that document.
Whenever the number of postings reaches a threshold, that can be defined by the user, "block_threhsold", the index will be written to a temporary file called block. When writing to that file, the terms are sorted and stored one per line. Each line contains a term followed by a list of document ids separated by a space(ex: term doc1 doc2). If the "positional" flag is set, the positions in a document are separated by a comma(ex: term doc1,pos1,pos2 doc2,pos1). 

After the entire file is indexed, the indexer will proceed to merge every temporary block file. First it reads a chunk of adjustable size for each block file. Every term and posting list in the blocks chunks are stored in a temporary dictionary. Only the terms that will not appear in another block can be written to disk sorted alphabetically. In order to do so, there is an list that keeps track of the last term read for each of the blocks. Since the blocks are also sorted, it is always garanteed that the "smallest" last term from that list is the last term that can be written. So, after there is an amount of terms that is higher than a defined threshold, the terms on the dictionary that are "smaller" than the "smallest" one on the list, will all be written to a file, which the name contains the first term and the last separated by a space(ex:"hello hi.txt")

When all the blocks are fully read, the indexer finishes its job by writing a few metadada files to a ".metadata" directory inside the indexed files directory.

In a file called "term_info.txt" it will store the posting list sizes for the correspondent term. If the flag "file_location" is set, then it will also store the position of the term in the indexed file for every step, which is defined in the parameter "file_location_step", meaning that every n terms there is another number pointing to its position in the indexed file.

If the flag "doc_rename" is set, then the file "doc_ids.txt" is also saved. This file contains a correspondance between a number and the document id. When indexing the number will be written to disk instead of the id of the document. 

Finally, the indexer needs to save its configuration for it to load whenever it neads to perform a query. This file is saved as "config.json". 

 
 ## Results



## How to run

The indexer and tokinizer provide the user a range of different options to customize the way they work. Files can be runned providing the desired parameters via terminal or by using a configuration file.

### Indexer

The indexer has a few options:

--positional
```
    -p 
```
when provided, saves the terms' positions in a document. This increases the required RAM and disk space, but can give better results when searching for a phrase.

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
