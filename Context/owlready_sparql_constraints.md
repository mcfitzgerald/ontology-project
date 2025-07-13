# SPARQL queries

Since version 0.30, Owlready proposes 2 methods for performing SPARQL
queries: the native SPARQL engine and RDFlib.

## Native SPARQL engine

The native SPARQL engine automatically translates SPARQL queries into
SQL queries, and then run the SQL queries with SQLite3.

The native SPARQL engine has better performances than RDFlib (about 60
times faster when tested on Gene Ontology, but it highly depends on
queries and data). It also has no dependencies and it has a much shorter
start-up time.

However, it currently supports only a subset of SPARQL.

### SPARQL elements supported

- SELECT, INSERT and DELETE queries
- UNION
- OPTIONAL
- FILTER, BIND, FILTER EXISTS, FILTER NOT EXISTS
- GRAPH clauses
- SELECT sub queries
- VALUES in SELECT queries
- All SPARQL functions and aggregation functions
- Blank nodes notations with square bracket, e.g. \'\[ a XXX\]\'
- Parameters in queries (i.e. \'??\' or \'??1\')
- Property path expressions, e.g. \'a/rdfs:subClassOf\*\', excepted
  those listed below

### SPARQL elements not supported

- ASK, DESCRIBE, LOAD, ADD, MOVE, COPY, CLEAR, DROP, CONSTRUCT queries

- INSERT DATA, DELETE DATA, DELETE WHERE queries (you may use INSERT or
  DELETE instead)

- SERVICE (Federated queries)

- FROM, FROM NAMED keywords

- MINUS

- Property path expressions with parentheses of the following forms:

  - nested repeats, e.g. (a/p\*)\*
  - sequence nested inside a repeat, e.g. (p1/p2)\*
  - negative property set nested inside a repeat, e.g. (!(p1 \| p2))\*

  i.e. repeats cannot contain other repeats, sequences and negative
  property sets.

DELETE queries are supported; contrary to INSERT queries, they do not
need to specify the ontology from which RDF triples are deleted.

    >>> default_world.sparql("""
            DELETE { ?r ?p ?o . }
            WHERE  {
                ?x rdfs:label "membrane" .
                ?x rdfs:subClassOf ?r .
                ?r a owl:Restriction .
                ?r ?p ?o .
            }
            """)

The native SPARQL engine supports queries with both a DELETE and an
INSERT statement.

### Parameters in SPARQL queries

Parameters allow to run the same query multiple times, with different
parameter values. They have two interests. First, they increase
performances since the same query can be reused, thus avoiding to parse
new queries. Second, they prevent security problems by avoiding SPARQL
code injection, e.g. if a string value includes quotation marks.

Parameters can be included in the query by using double question marks,
e.g. \"??\". Parameter values can be Owlready entities or datatype
values (int, float, string, etc.). Parameter values are passed in a list
after the query:

    >>> list(default_world.sparql("""
               SELECT ?y
               { ?? rdfs:subClassOf* ?y }
        """, [mito_inher]))
    [[obo.GO_0000001], [obo.GO_0048308], [obo.GO_0048311],
     [obo.GO_0006996], [obo.GO_0007005], [obo.GO_0051646],
     [obo.GO_0016043], [obo.GO_0051640], [obo.GO_0009987],
     [obo.GO_0071840], [obo.GO_0051641], [obo.GO_0008150],
     [obo.GO_0051179]]

Parameters can also be numbered, e.g. \"??1\", \"??2\", etc. This is
particularly usefull if the same parameter is used multiple times in the
query.

    >>> list(default_world.sparql("""
               SELECT ?y
               { ??1 rdfs:subClassOf* ?y }
        """, [mito_inher]))
    [[obo.GO_0000001], [obo.GO_0048308], [obo.GO_0048311],
     [obo.GO_0006996], [obo.GO_0007005], [obo.GO_0051646],
     [obo.GO_0016043], [obo.GO_0051640], [obo.GO_0009987],
     [obo.GO_0071840], [obo.GO_0051641], [obo.GO_0008150],
     [obo.GO_0051179]]

Finally, Owlready also accepts lists as parameter values, when the
parameter is used with the \'IN\' (or \'NOT IN\') operator, e.g.:

    >>> q = world.prepare_sparql("""
    SELECT ?x {
        ?x rdfs:label ?label .
        FILTER(?label IN ??)
    }
    """)
    >>> list(q.execute([["label1", "label2"]]))

### Non-standard additions to SPARQL

The following functions are supported by Owlready, but not standard:

> - The SIMPLEREPLACE(a, b) function is a version of REPLACE() that does
>   not support Regex. It works like Python or SQLite3 replace, and has
>   better performances.
> - THE LIKE(a, b) function performs similarly to the SQL Like operator.
>   It is more limited, but faster than the Regex SPARQL functions.
> - THE FTS(a, b) function performs a Full-text-Search (FTS), allowing
>   for very fast text searching. Please refer to the Full Text Search
>   documentation in the `annotations`{.interpreted-text role="doc"}
>   chapter.
> - The NEWINSTANCEIRI() function create a new IRI for an instance of
>   the class given as argument. This IRI is similar to those created by
>   default by Owlready. Note that the function creates 2 RDF triples,
>   asserting that the new individual is an OWL NamedIndividual and an
>   instance of the desired class passed as argument.
> - The LOADED(iri) function returns True if the entity with the given
>   IRI is currently loaded in Python, and False otherwise.
> - The STORID(iri) function returns the integer Store-ID used by
>   Owlready in the quadstore for representing the entity.
> - The DATE(), TIME() and DATETIME() functions can be used to handle
>   date and time. They behave as in SQLite3 (see
>   <https://www.sqlite.org/lang_datefunc.html>).
> - The DATE_SUB(), DATE_ADD(), DATETIME_SUB and DATETIME_ADD()
>   functions can be used to substract or add a time duration to a date
>   or a datetime, for example : DATETIME_ADD(NOW(),
>   \"P1Y\"\^\^xsd:duration)

In Owlready, INSERT and DELETE queries can have a GROUP BY, HAVING
and/or ORDER BY clauses. This is normally not allowed by the SPARQL
specification.
