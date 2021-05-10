const express = require('express')
const bodyParser = require('body-parser')
const app = express()
const db = require('./queries')
const port = 3000

app.use(bodyParser.json())
app.use(
  bodyParser.urlencoded({
    extended: true,
  })
)

app.get('/', (request, response) => {
  response.json({ info: 'Fingerprin DB Ok' })
})

app.get('/users', db.getUsers)
app.get('/users/:id', db.getUserById)
app.post('/users', db.createUser)
app.put('/users/:id', db.updateUser)
app.delete('/users/:id', db.deleteUser)

app.get('/attendances', db.getAttendances)
app.get('/attendances/:id', db.getAttendancesById)
app.post('/attendances', db.createAttendances)
app.put('/attendances/:id', db.updateAttendances)
app.delete('/attendances/:id', db.deleteAttendances)

app.listen(port, () => {
  console.log(`App running on port ${port}.`)
})
