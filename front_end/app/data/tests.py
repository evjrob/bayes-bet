from django.urls import reverse
from django.http import HttpResponse, JsonResponse

# tests for views


class GetGamesTest:
    
    def test_get_games_date(self):
        """
        This test ensures that games exist when we make a GET request to 
        the game/date endpoint
        """
        # hit the API endpoint
        response = self.client.get(
            reverse("games-all", kwargs={"version": "v1", 'date': '2019-04-15'})
        )
        # fetch the data from db
        expected = [2018030123, 2018030133, 2018030153, 2018030173]
        serialized = JsonResponse({"data" : expected})
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)