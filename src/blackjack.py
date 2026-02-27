from random import shuffle

class BlackjackGame:
    def __init__(self):
        self.games = {}

    def start_game(self, chat_id, user_id):
        deck = self._create_deck()
        shuffle(deck)
        self.games[chat_id] = {
            "deck": deck,
            "dealer_hand": [deck.pop(), deck.pop()],
            "player_hand": [deck.pop(), deck.pop()],
            "user_id": user_id,
        }

    def hit(self, chat_id, user_id):
        game = self.games.get(chat_id)
        if not game or game["user_id"] != user_id:
            return "No active game found."
        game["player_hand"].append(game["deck"].pop())
        return self._hand_status(game)

    def stand(self, chat_id, user_id):
        game = self.games.get(chat_id)
        if not game or game["user_id"] != user_id:
            return "No active game found."
        while self._hand_value(game["dealer_hand"]) < 17:
            game["dealer_hand"].append(game["deck"].pop())
        return self._determine_winner(game)

    def _create_deck(self):
        cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
        suits = ["♠", "♥", "♦", "♣"]
        return [f"{card}{suit}" for card in cards for suit in suits]

    def _hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            if card[:-1] in ["J", "Q", "K"]:
                value += 10
            elif card[:-1] == "A":
                aces += 1
                value += 11
            else:
                value += int(card[:-1])
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def _hand_status(self, game):
        player_value = self._hand_value(game["player_hand"])
        if player_value > 21:
            return f"Bust! Your hand: {game['player_hand']}"
        return f"Your hand: {game['player_hand']}, Dealer's card: {game['dealer_hand'][0]}"

    def _determine_winner(self, game):
        player_value = self._hand_value(game["player_hand"])
        dealer_value = self._hand_value(game["dealer_hand"])
        if player_value > 21:
            return f"Bust! You lose. Dealer's hand: {game['dealer_hand']}"
        elif dealer_value > 21 or player_value > dealer_value:
            return f"You win! Dealer's hand: {game['dealer_hand']}"
        elif player_value < dealer_value:
            return f"You lose. Dealer's hand: {game['dealer_hand']}"
        else:
            return f"It's a tie! Dealer's hand: {game['dealer_hand']}"