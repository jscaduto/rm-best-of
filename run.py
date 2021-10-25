import csv
import statistics
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Rating:
    album: str
    rank: Union[int, str]
    source: str
    score: Optional[float] = None


@dataclass
class Review:
    source: str
    ratings: List[Rating]
    honorable_mentions: List[Rating]

    def add_rating(self, rating):
        if rating.rank == 'hm':
            self.honorable_mentions.append(rating)
        else:
            super().add_rating(rating)


@dataclass
class UnrankedReview(Review):

    def calculate_scores(self):
        scores = [
            # todo: should this equation be...
            #       1.5 - ((x - 1) * .01)
            1.5 - (x * .01)
            for x in range(1, len(self.ratings))
        ]
        median_score = statistics.median(scores)
        for rating in self.ratings:
            rating.score = median_score
        for rating in self.honorable_mentions:
            rating.score = median_score - .1


@dataclass
class RankedReview(Review):

    def calculate_scores(self):
        for rating in self.ratings:
            rating.score = 1.5 - ((rating.rank - 1) * .01)
        for rating in self.honorable_mentions:
            rating.score = 1.5 - (len(self.ratings) * .01)


@dataclass
class CompositeRating:
    album: str
    ratings: List[Rating]

    @property
    def number_of_appearances(self):
        return len(self.ratings)

    @property
    def count_of_number_one_rankings(self):
        count = 0
        for rating in self.ratings:
            if rating.rank == 1:
                count += 1
        return count

    @property
    def rank_by_source(self):
        return {
            rating.source: rating.rank
            for rating in self.ratings
        }

    @property
    def score(self):
        result = 0
        for rating in self.ratings:
            result += rating.score
        return result


def create_ratings():
    ratings = []
    with open('2020.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rank = None
            try:
                rank = int(row['Rank'])
            except ValueError:
                rank = row['Rank']
            ratings.append(
                Rating(
                    album=row['Album'],
                    rank=rank,
                    source=row['Source'],
                )
            )
    return ratings


def create_reviews(ratings):
    ratings_by_source = dict()
    for rating in ratings:
        if rating.source in ratings_by_source:
            ratings_by_source[rating.source].append(rating)
        else:
            ratings_by_source[rating.source] = [rating]
    reviews = []
    for source, ratings in ratings_by_source.items():
        ranked_ratings = []
        unranked_ratings = []
        honorable_mentions = []
        for rating in ratings:
            if type(rating.rank) == int:
                ranked_ratings.append(rating)
            elif rating.rank == 'x':
                unranked_ratings.append(rating)
            elif rating.rank == 'hm':
                honorable_mentions.append(rating)
            else:
                print(f'Bad data: {rating}')
                exit(1)
        if ranked_ratings and unranked_ratings:
            print(f'ERROR: Source "{source}" has both ranked and unranked ratings.')
            exit(1)
        elif ranked_ratings:
            review = RankedReview(
                source=source,
                ratings=ranked_ratings,
                honorable_mentions=honorable_mentions,
            )
        elif unranked_ratings:
            review = UnrankedReview(
                source=source,
                ratings=unranked_ratings,
                honorable_mentions=honorable_mentions,
            )
        review.calculate_scores()
        reviews.append(review)
    return reviews


def create_composite_ratings(ratings):
    composite_ratings_by_album = {}
    for rating in ratings:
        if rating.album in composite_ratings_by_album:
            composite_ratings_by_album[rating.album].ratings.append(rating)
        else:
            composite_ratings_by_album[rating.album] = CompositeRating(
                album=rating.album,
                ratings=[rating],
            )
    return composite_ratings_by_album.values()


def create_composite_csv(composite_ratings, sources):
    with open('output.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            'album',
            'composite score',
            'list appearances',
            '#1 appearances',
            *sources
        ])
        writer.writeheader()
        for composite_rating in composite_ratings:
            writer.writerow({
                'album': composite_rating.album,
                'composite score': composite_rating.score,
                'list appearances': composite_rating.number_of_appearances,
                '#1 appearances': composite_rating.count_of_number_one_rankings,
                **composite_rating.rank_by_source,
            })


ratings = create_ratings()
sources = set([
    rating.source
    for rating in ratings
])
reviews = create_reviews(ratings)
composite_ratings = create_composite_ratings(ratings)
create_composite_csv(composite_ratings, sources)
