const Pool = require('pg').Pool
const pool = new Pool({
  user: 'szm219',
  host: 'localhost',
  database: 'fingerdata',
  password: 'szm219',
  port: 5432,
})

const getUsers = (request, response) => {
  pool.query('SELECT * FROM users ORDER BY id ASC', (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).json(results.rows)
  })
}

const getUserById = (request, response) => {
  const id = parseInt(request.params.id)

  pool.query('SELECT * FROM users WHERE id = $1', [id], (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).json(results.rows)
  })
}

const createUser = (request, response) => {
  const { reader_id, data_id, user_category, name, eigen_values} = request.body

  pool.query('INSERT INTO users (reader_id, data_id, user_category, name, eigen_values, register_date) VALUES ($1, $2, $3, $4, $5 current_timestamp) RETURNING ID', 
    [reader_id, data_id, user_category, name, eigen_values], (error, results) => {
    if (error) {
      throw error
    }
    response.status(201).send(`User added with ID: ${results.rows[0].id}`);
  })
}

const updateUser = (request, response) => {
  const id = parseInt(request.params.id)
  const { reader_id, data_id, user_category, name, eigen_values} = request.body

  pool.query(
    'UPDATE users SET reader_id = $1, data_id = $2, user_category = $3, name = $4, eigen_values = $5, register_date = current_timestamp WHERE id = $6',
    [reader_id, data_id, user_category, name, eigen_values, id],
    (error, results) => {
      if (error) {
        throw error
      }
      response.status(200).send(`User modified with ID: ${id}`)
    }
  )
}

const deleteUser = (request, response) => {
  const id = parseInt(request.params.id)

  pool.query('DELETE FROM users WHERE id = $1', [id], (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).send(`User deleted with ID: ${id}`)
  })
}

const getAttendances = (request, response) => {
  pool.query('SELECT * FROM attendances ORDER BY id ASC', (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).json(results.rows)
  })
}

const getAttendancesById = (request, response) => {
  const id = parseInt(request.params.id)

  pool.query('SELECT * FROM attendances WHERE id = $1', [id], (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).json(results.rows)
  })
}

const createAttendances = (request, response) => {
  const { reader_id, data_id, user_category, name, register_type } = request.body

  pool.query('INSERT INTO attendances (reader_id, data_id, user_category, name, register_type, register_date) VALUES ($1, $2, $3, $4, $5 current_timestamp) RETURNING ID',
    [reader_id, data_id, user_category, name, register_type], (error, results) => {
    if (error) {
      throw error
    }
    response.status(201).send(`attendance added with ID: ${results.rows[0].id}`);
  })
}

const updateAttendances = (request, response) => {
  const id = parseInt(request.params.id)
  const { reader_id, user_category, name, register_type} = request.body

  pool.query(
    'UPDATE users SET reader_id = $1, data_id = $2, user_category = $3, name = $4, register_type = $5, register_date = current_timestamp WHERE id = $6',
    [reader_id, data_id, user_category, name, register_type, id],
    (error, results) => {
      if (error) {
        throw error
      }
      response.status(200).send(`User modified with ID: ${id}`)
    }
  )
}

const deleteAttendances = (request, response) => {
  const id = parseInt(request.params.id)

  pool.query('DELETE FROM attendances WHERE id = $1', [id], (error, results) => {
    if (error) {
      throw error
    }
    response.status(200).send(`attendance deleted with ID: ${id}`)
  })
}


module.exports = {
  getUsers,
  getUserById,
  createUser,
  updateUser,
  deleteUser,
  getAttendances,
  getAttendancesById,
  createAttendances,
  updateAttendances,
  deleteAttendances,
}


