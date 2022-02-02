

# RI Project <!-- omit in toc -->
## Authors <!-- omit in toc -->

[Bruno Bastos](https://github.com/BrunosBastos)\
[Leandro Silva](https://github.com/leand12)


## Table of Contents <!-- omit in toc -->
- [How it works](#how-it-works)
  - [Tokenizer](#tokenizer)
  - [Indexer](#indexer)
  - [Ranking](#ranking)
    - [VSM](#vsm)
    - [BM25](#bm25)
- [Results](#results)
  - [Indexing](#indexing)
  - [Ranking](#ranking-1)
    - [VSM](#vsm-1)
    - [BM25](#bm25-1)
  - [Boost](#boost)
    - [BM25 without Boost](#bm25-without-boost)
    - [BM25 with Boost](#bm25-with-boost)
- [How to run](#how-to-run)
  - [Indexer](#indexer-1)
  - [Tokenizer](#tokenizer-1)
  - [Ranking](#ranking-2)



## How it works

There are 3 important files in this project: tokenizer.py, indexer.py and query.py.


### Tokenizer

The tokenizer is responsible for the processing of tokens in a document. Its main functionalities
are transforming the tokens into terms and pass those terms to the indexer together with the information of the document, such as ID and position of the token.

There are multiple strategies that are being used here.
The tokenizer reads one document at a time and, after selecting the required fields, it splits the text word by word, where each word is split by a space.

With this list of tokens, it then normalizes each token, transforming it into a term.
Every token that has a non-alphanumeric character, will have that character replace by a space, and then the tokens are split, forming more tokens.
The user can set the minimum length of a token and those that are smaller than that number will be discarded.
A stopword file containing the tokens that should be discarded can be provided by the user, but it is not necessary.
There can also be provided a list of contractions, which is mostly used in English, that will transform contractions into the respective tokens (e.g.: I've ⇾ I have).
There is an option to remove every token that is a number, integer or float.
It is used case folding to make each token lowercase and transform some letters into others.
Finally, the remaining tokens will go through the stemmer and the result will be a list of terms.

The list of terms is then given to the indexer with the positional information of the term and the document ID.


### Indexer

The indexer makes use of the list of terms provided by the tokenizer and starts the indexing process.
Every term is stored in a hash table (dictionary) together with the list of postings(list with the IDs of the documents where the term appears). If the "positional" flag is set, instead of storing a postings' list, it is stored for each term a dictionary with the document ID and a respective list of positions where that term appears in that document.
Whenever the number of postings reaches a threshold, that can be defined by the user, "block_threhsold", the index will be written to a temporary file called block. When writing to that file, the terms are sorted and stored one per line. Each line contains a term followed by a list of document IDs separated by a space (e.g.: term doc1 doc2). If the "positional" flag is set, the positions in a document are separated by a comma(e.g.: term doc1,pos1,pos2 doc2,pos1). 

After the entire file is indexed, the indexer will proceed to merge every temporary block file. First, it reads a chunk of adjustable size for each block file. Every term and posting list in the blocks chunks are stored in a temporary dictionary. Only the terms that will not appear in another block can be written to disk, sorted alphabetically. In order to do so, there is a list that keeps track of the last term read for each of the blocks. Since the blocks are also sorted, it is always guaranteed that the "smallest" last term from that list is the last term that can be written. So, after there is an amount of terms that is higher than a defined threshold, the terms on the dictionary that are "smaller" than the "smallest" one on the list, will all be written to a file, which the name contains the first term and the last separated by a space (e.g.: "hello hi.txt")

When all the blocks are fully read, the indexer finishes its job by writing a few metadata files to a ".metadata" directory inside the indexed files' directory.

In a file called "term_info.txt" it will store the posting list sizes for the correspondent term. If the flag "file_location" is set, then it will also store the position of the term in the indexed file for every step, which is defined in the parameter "file_location_step", meaning that every n terms there is another number pointing to its position in the indexed file.

If the flag "doc_rename" is set, then the file "doc_ids.txt" is also saved. This file contains a correspondence between a number and the document ID. When indexing the number will be written to disk instead of the ID of the document. 

Finally, the indexer needs to save its configuration for it to load whenever it neads to perform a query. This file is saved as "config.json". 

 
### Ranking

There are 2 available ranking algorithms: VSM (Vector Space Model) and BM25 (Best Matching). The indexer uses the selected algorithm to rank the documents for a given query. The algorithms are choosed while indexing the dataset and in order to be swapped(or to change any of its parameters), it requires the indexer to index the dataset again.

#### VSM

VSM has 2 parameters, `p1` and `p2`, that correspond to the schema that will be used when calculating the weights for the rankibg algorithm. P1 defines the schema for the weigths of terms in the documents, while P2 defines the weights of the terms in the query. The indexer supports different values for P1 and P2.

P1
```
l n c
l n n
n n c
```
the first letter can be `l/n` and the last letter can be `c/n`. The middle letter can only be `n`.


P2
```
l t c
l t n
l n c
l n n
n t c
n t n
n n c
```

the first letter can be `l/n`, the middle letter can be `t/n` and the last letter can be `c/n`.

The default values for p1 and p2 are `lnc` and `ltc` respectively.


#### BM25

BM25 also has 2 parameters called `k1` and `b`, with default values `1.2` and `0.75`.

 ## Results


### Indexing
There were conducted some experiments with different configurations in order to see their tradeoffs and benefits. This table shows for each experiment the configurations that were used.


| Experiment | positional               | save_zip                 | rename_doc               | case_folding             | no_numbers               | stopwords                | contractions             | stemmer                  |
| ---------- | ------------------------ | ------------------------ | ------------------------ | ------------------------ | ------------------------ | ------------------------ | ------------------------ | ------------------------ |
| config    | :heavy_multiplication_x: | :heavy_check_mark: | :heavy_multiplication_x: | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_multiplication_x: |
| config 0   | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: |
| config 1   | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_multiplication_x: |
| config 2   | :heavy_multiplication_x: | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       |
| config 3   | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       |
| config 4   | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       |
| config 5   | :heavy_multiplication_x: | :heavy_multiplication_x:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       | :heavy_check_mark:       |

The experiments in this table used the dataset: amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz (26.2 MB), after it was unzipped.

| Experiment | Indexing Time | Vocabulary Size | Index Size on Disk | # of Index segments | Start-Up Time |
| ---------- | ------------- | --------------- | ------------------ | ------------------- | ------------- |
| config     | 25.80s        | 70449           | 36.88MB            | 6                   | 0.12s         |
| config 0   | 22.39s        | 95447           | 80.36MB            | 8                   | 0.19s         |
| config 1   | 20.94s        | 70449           | 59.69MB            | 6                   | 0.12s         |
| config 2   | 79.72s        | 49352           | 13.80MB            | 6                   | 0.17s         |
| config 3   | 92.92s        | 49352           | 20.76MB            | 6                   | 0.19s         |
| config 4   | 76.86s        | 49352           | 56.68MB            | 6                   | 0.07s         |
| config 5   | 79.50s        | 49352           | 28.04MB            | 6                   | 0.16s         |


Analysing the results, we can see that using the stemmer decreases the vocabulary size, as there are more different tokens that are transformed in equal terms. However, this is paid off with a higher indexing time.

The positional approach stores more information to show the exact location of a token in a document, and for that it is reasonable to say that it takes more indexing time and space on disk.

Finally, when compressing the index files, we can see that the space taken on disk is reduced considerably without affecting too much in the start-up time.


| Experiment | Indexing Time | Vocabulary Size | Index Size on Disk | # of Index segments | Start-Up Time |
| ---------- | ------------- | --------------- | ------------------ | ------------------- | ------------- |
| dataset 1    | 25.80s        | 70449           |36.88MB            | 6                   | 0.12s         |
| dataset 2    | 352.55 s      | 330932          | 306.86MB           | 9                   | 0.71s         |
| dataset 3    | 2325.17s      | 1133238         | 1.95GB             | 15                  | 1.67s         |
| dataset 4    | 4521.89s      | 1330785         | 4.10GB             | 25                   | 2.54s         |

For all the datasets, it was use the first config file on the first table. The thresholds for the blocks to be written to disk were changed based on the size of the file. So, the size of a block on the first dataset is much smaller than the size of a block in the last dataset. 


### Ranking

Both the ranking algorithms create an overhead in the indexer, increasing the time and space required. However, as some optimizations were made, comparing the overhead with the previous results is hard.

For the ranking algorithms, especially for the VSM schemas, we experimented different parameters, but the queries execution times remained almost the same.


| Dataset | Ranking Algorithm | Indexing Time | Vocabulary Size | Index Size on Disk | Start-Up Time | Query Time |
| ---------- | ------------- | ------------ | --------------- | ------------------ | ------------------- | ------------- |
| digital_video_games  |  VSM   | 79.27s        | 70449           | 30.55MB            | 0.20s                  | 1.62s        |
| digital_music  |  VSM   | 686.23s       | 330932          | 269.33MB           | 1.56s                  | 10.72s       |
| digital_video_games  |  BM25  | 60.50s        | 70449           | 29.09MB            | 0.20s                  | 1.51s        |
| digital_music  |  BM25  | 555.24s       | 330932          | 241.59MB           | 1.56s                  | 9.25s        |


The results with the ranked documents for each query are stored in the `queries` folder. The name of the file represents the ranking algorithm used as well as the provided parameters for that algorithm. 


To examine the obtained results for each algorithm we checked the most relevant documents for a given query, aswell as the least relevant ones and saw if that made sense. 

#### VSM

For the query `greatest rock album` when using the digital_video_games dataset (VSM lnc.ltc), the most relevant document was `RYM5TBY7AB0SX` and the least relevant was `R119IW6ZFAST2M`.

Using our tokenizer, the most relevant document has the following terms: `xbox live points card rock rock comments` and since we are taking into consideration if a term appears more than once, this document has 2/7 relevant terms. In comparison, the least relevant has `payne great game payne best love game because huge payne series awesome graphics rock solid story line` which has 1/17 relevant terms for the query. 

#### BM25

For the query `greatest rock album` when using the digital_video_games dataset with BM25, k1 = 1.2, b = 0.75, the most relevant document was `RCDO6KF1N4DJX` and the least relevant was `R119IW6ZFAST2M`.

Using our tokenizer, the most relevant document has in total **115 terms**, where **5 terms** math the query. BM25 also has into consideration the length of the document, and when compared to the other ones above, for example, this one is much bigger. 

In comparison, the least relevant (which, by coincidende, is the same in VSM rank) has only **1 term** in **17 terms** that matches the query. This is because it is a small document, which is penalized by the BM25 ranking.


### Ranking Accuracy

#### BM25 without Boost

Query Throughput: 0.97 queries/second

Query Execution Time: 1.03 seconds/query

Total time taken to search for all queries: 15.44 seconds


Metrics for all queries
 | Top K  |  Precision |   Recall  |  F-Measure  |  Average Precision  |  NDCG|
|-------  |----------- | --------  |-----------  |-------------------  |------|
 |10  |      0.860 |    0.118  |      0.207  |              0.927  | 0.763|
 |20  |      0.793 |    0.218  |      0.340  |              0.871  | 0.735|
| 50  |      0.617 |    0.420  |      0.497  |              0.769  | 0.690|


#### BM25 with Boost


Query Throughput: 0.44 queries/second

Query Execution Time: 2.29 seconds/query

Total time taken to search for all queries: 34.38 seconds


Metrics for all queries                                                   
|  Top K |   Precision  |  Recall   | F-Measure   | Average Precision|    NDCG   |
|------- | ----------- | -------- | ----------- | -------------------  |------   |
| 10   |     0.947   |  0.130    |    0.229    |            0.970  | 0.843   |
| 20   |     0.893   |  0.245    |    0.384    |            0.943  | 0.819   |
| 50   |     0.680   |  0.460    |    0.546    |            0.844  | 0.760   |


#### VSM without Boost

Query Throughput: 1.01 queries/second

Query Execution Time: 0.99 seconds/query

Total time taken to search for all queries: 14.86 seconds


Metrics for all queries
 | Top K  |  Precision |   Recall  |  F-Measure  |  Average Precision  |  NDCG|
|-------  |----------- | --------  |-----------  |-------------------  |------|
 |10  |      0.993 |    0.138  |      0.241  |              0.999  | 0.880|
 |20  |      0.983 |    0.273  |      0.426  |              0.991  | 0.885|
| 50  |      0.877 |    0.605  |      0.712  |              0.957  | 0.876|


#### VSM with Boost


Query Throughput: 0.45 queries/second

Query Execution Time: 2.23 seconds/query

Total time taken to search for all queries: 33.45 seconds


Metrics for all queries                                                   
|  Top K |   Precision  |  Recall   | F-Measure   | Average Precision|    NDCG   |
|------- | ----------- | -------- | ----------- | -------------------  |------   |
| 10   |     0.987   |  0.137    |    0.240    |            0.993  | 0.869   |
| 20   |     0.957   |  0.264    |    0.413    |            0.985  | 0.862   |
| 50   |     0.813   |  0.559    |    0.659    |            0.923  | 0.843   |


<!--
VSM
args    lnc.ltc
                games           music

index time      79.27 seconds   686.23 seconds
vocabulary      70942           362981
index disk      30.55 MB (4.3)  269.33 MB (41.1)
segments        6               48
startup         0.20 seconds    1.56 seconds
queries         1.62 seconds    10.72 seconds

BM25
args    0.75 1.2
                games           music

index time      60.50 seconds   555.24 seconds
vocabulary      70942           362981
index disk      29.09 MB (4.3)  241.59 MB (41.1)
segments        6               48
startup         0.20 seconds    1.56 seconds
queries         1.51 seconds    9.25 seconds
-->

## How to run

This program has 2 modes to run, one to create an indexer from a dataset, and another to search in a pre-created indexer.

In the `index` mode, the user can use a wide range of different options in the terminal to customize the indexer, tokenizer and ranking. Alternatively, the user can pass a configuration file with all the customizable options.

In the `search` mode, the user can search some queries in a pre-created indexer.

For additional information, run the program with the help argument for the respective mode.

**Note:** if the provided dataset file is a `.gz` file, it will unzip it as it reads.


Examples:


- To create an indexer, and optionally with some arguments, use:
```
python3 main.py index ../dataset [OPTIONS ...]
```
where `../dataset` is the path of the dataset.


- To create an indexer with a config file use:
```
python3 main.py index ../dataset -c config.json 
```
where `config.json` is the path of the config file.


- To run a pre-created indexer, use:
```
python3 main.py search indexer/
```
where `indexer/` is the path to the created indexer folder.


### Indexer

The indexer has a few options:

`--positional`\
when provided, saves the terms' positions in a document. This increases the required RAM and disk space, but can give better results when searching for a phrase.

`--save-zip`\
when provided, the output files of the indexer will be zipped. This saves disk space in exchange for a slower read whenever a user is making a query.

`--rename-doc`\
when provided, the documents will be renamed as an integer which occupies less bytes to store. For a smaller number of documents, this will decrease the space required to store the indexer, but in exchange, will consume a bit more space in RAM. For larger number of documents, it will not work, as it will end up needing more space to store a single document.

`--file-location-step [STEP]`\
when provided, the location of a term in a file will be stored in memory and later send to disk. This will increase the speed at which the indexer accesses a certain term, but will need more disk storage and RAM. The step corresponds to the number of terms that are skipped in order to save the next file position. A bigger step will result in a slower search but decreases the disk space required to save the positions. A step of 1 keeps the position for every term in the corresponding file.

`--block-threshold THRESHOLD`\
corresponds to the maximum number of documents that can be stored in a block. A smaller value will result in more files, slowing down the merge and takes more time writing to disk. While if a higher value is chosen, the indexer can run out of RAM.

`--merge-threshold THRESHOLD`\
corresponds to the maximum number of postings for a merged file in disk. The higher the value, lesser files will be created, but can slow down search as there are bigger files to look for the terms.

`--merge-dir DIR`\
the final directory where the indexer is stored. This directory should contain a ".metadata" directory containing the necessary metadata files required for the indexer to be loaded.


### Tokenizer

The tokenizer parameters will decide how the tokens are processed.

`--case-folding`\
chooses whether to convert every token to lowercase.

`--no-numbers`\
discards every token that is a number.

`--stemmer`\
makes use of the Snowball stemmer for English words.

`--min-length LENGTH`\
only tokens with size greater or equal to the minimum length value are accounted.

`--stopwords-file FILE`\
discards every word that is contained in the stopwords file.

`--contractions-file FILE`\
uses a contraction file that has many English contractions. If a token matches one of the contractions, it is converted to the non-contracted correspondent token.


### Ranking

`--name {VSM,BM25}`\
the type of the ranking that the indexer has to follow when running a query.

`-p1 SCHEME`\
the weighting scheme in SMART notation for the document. Used by VSM.

`-p2 SCHEME`\
the weighting scheme in SMART notation for the query. Used by VSM.

`-k1 N`\
controls the term frequency scaling. k1 = 0 is a binary model, while a large k1 is a raw term frequency. Typically, k1 is set around 1.2–2. Used by BM25.

`-b N`\
controls the document length normalization. b = 0 is no length normalization, while b = 1 is relative frequency. Typically, b around 0.75. Used by BM25.
