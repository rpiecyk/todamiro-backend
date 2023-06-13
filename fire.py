import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.ApplicationDefault()
TOPICS = '_topics'


class Fire():
    def __init__(self) -> None:
        self.app = firebase_admin.initialize_app()
        self.db = firestore.client()

    def fetch_topics(self):
        users_ref = self.db.collection(TOPICS)
        tops = []
        for top in users_ref.stream():
            tops.append(top.to_dict())
        print(tops)
        return tops
    
    def put_topic(self,name,jload):
        top_ref = self.db.collection('_topics').document(name)
        jload['slotsTaken'] = 1
        top_ref.set(jload)


# cols = db.collections()
# for c in cols:
#     print(c.id, c)

# test = False

# if test:
#     doc_ref = db.collection('users').document('alovelace')
#     doc_ref.set({'first':'Ada','last':'Lovelace','born':1815})

#     doc_ref = db.collection('users').document('aturing')
#     doc_ref.set({'first':'Alan','middle':'Mathison','last':'Turing','born':1912})



# for doc in docs:
    # print(f'{doc.id} => {doc.to_dict()}')
