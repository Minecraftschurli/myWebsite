import json
from operator import itemgetter


class ShootItData(object):
    def __init__(self):
        self.data = json.load(open('./data/games/shoot_users.json'))
        self.refresh()

    def refresh(self):
        for i in range(len(self.data['users'])):
            if 'check' in self.data['users'][i]:
                del self.data['users'][i]['check']
        with open('./data/games/shoot_users.json', 'w+') as file:
            json.dump(self.data, file, indent=2)
            file.seek(0)
            self.data = json.load(file)

    def get_data_for_user(self, user):
        for user_data in self.data['users']:
            if user_data['linked_user'] == user:
                return user_data
        return None

    def get_anonymus_user(self, user):
        for user_data in self.data['users']:
            if user_data['username'] == user:
                return user_data
        return None

    def user_exists(self, user):
        for user_data in self.data['users']:
            if user_data['username'] == user:
                return True
        return False

    def create_and_get_user(self, user, **kwargs):
        if user is None:
            if kwargs['assoc'] is not None:
                user = kwargs['assoc']
            else:
                return None
        new_user = {'username': user, 'linked_user': kwargs['assoc']}
        for diff in self.data['difficulties']:
            new_user[diff] = 0
        self.data['users'].append(new_user)
        self.data['difficulties']['easy'].append((user, 0))
        self.data['difficulties']['medium'].append((user, 0))
        self.data['difficulties']['hard'].append((user, 0))
        self.data['difficulties']['impossible'].append((user, 0))
        self.refresh()
        return self.get_anonymus_user(user)

    def get_highscores(self, difficulty, length=10):
        out = self.data['difficulties'][difficulty.lower()]
        out = [x for x in out if x[0] != 'dummy']
        return out[:length]

    def update(self, user, difficulty, score):
        i = 0
        j = -1
        for user_data in self.data['users']:
            if user_data['username'] == user:
                self.data['users'][i][difficulty.lower()] = int(score)
                j = i
            i += 1
        i = 0
        for diff in self.data['difficulties'][difficulty.lower()]:
            if diff[0] == user:
                self.data['difficulties'][difficulty.lower()][i] = (self.data['users'][j]['username'], score)
            i += 1
        self.data['difficulties'][difficulty.lower()].sort(key=itemgetter(1), reverse=True)
        self.refresh()
