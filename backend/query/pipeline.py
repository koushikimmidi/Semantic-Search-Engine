from backend.query import (
    QueryExpander,
    SynonymExpander,
    SpellCorrector,
    QueryNormalizer,
    StopWordRemover,
    DomainVocabulary
)


class QueryPipeline:

    def __init__(self):

        self.normalizer = QueryNormalizer()

        self.stopwords = StopWordRemover()

        self.corrector = SpellCorrector()

        self.expander = QueryExpander()

        self.synonyms = SynonymExpander()

        self.domain = DomainVocabulary()

    def process(self, query):

        stages = {}

        stages["Original"] = query

        query = self.normalizer.normalize(query)

        stages["Normalized"] = query

        query = self.stopwords.remove(query)

        stages["Stop Words Removed"] = query

        query = self.corrector.correct(query)

        stages["Spell Corrected"] = query

        query = self.expander.expand(query)

        stages["Expanded"] = query

        query = self.synonyms.expand(query)

        stages["Synonyms"] = query

        query = self.domain.expand(query)

        stages["Domain Expanded"] = query

        return stages