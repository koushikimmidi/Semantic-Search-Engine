class SearchEvaluator:

    def compare(self, original, processed):

        print("\n" + "=" * 60)
        print("QUERY COMPARISON")
        print("=" * 60)

        print(f"Original Query  : {original}")
        print(f"Processed Query : {processed}")

        original_words = len(original.split())
        processed_words = len(processed.split())

        print(f"\nOriginal Words  : {original_words}")
        print(f"Processed Words : {processed_words}")

        print(f"Added Terms     : {processed_words - original_words}")