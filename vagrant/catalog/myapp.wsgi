from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://catalog:catalog2@35.171.4.160/library')

connection = engine.connect()
result = connection.execute("select name from catTest")
for row in result:
    print("name:", row['name'])
connection.close()

def application(environ, start_response):
    status = '200 OK'
    output = 'Hello Udacity!'

    response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]

