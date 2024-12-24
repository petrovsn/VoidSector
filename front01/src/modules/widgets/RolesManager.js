import React from 'react'
import { get_http_address } from '../network/connections'
import { timerscounter } from '../utils/updatetimers'
import { get_locales } from '../locales/locales'

export class RoleManagerWidget extends React.Component {
  constructor() {
    super()
    this.state = {
      data: {
        "captain": {}
      }
    }
  }

  componentDidMount() {
    let timer_id = timerscounter.get(this.constructor.name)
    if (!timer_id) {
      clearInterval(timer_id)
    }
    timer_id = setInterval(this.onUpdate, 1000)
    timerscounter.add(this.constructor.name, timer_id)
  }

  componentWillUnmount() {
    let timer_id = timerscounter.get(this.constructor.name)
    clearInterval(timer_id)
  }


  onUpdate = () => {
    var myInit = {
      method: "GET",
      headers: {}
    }

    return fetch(get_http_address() + "/users/roles/table", myInit)
      .then(response => {
        let code = response.status;
        if (code === 200) {
          return response.json()
        }

      }).then(data => {
        if (data) {
          this.setState({ 'data': data })

        }
      }).catch(error => {
        console.error('There is some error', error);
      });
  }

  onAssignRole = (username, role, state) => {
    var myInit = {
      method: "PUT",
      headers: {
        'Username': username,
        'Role': role,
        'State': state
      }
    }

    return fetch(get_http_address() + "/users/roles/role", myInit)
      .then(response => {
        let code = response.status;
        if (code === 200) {
          return response.json()
        }

      }).then(data => {
        if (data) {
          this.setState({ 'data': data })

        }
      })
  }

  is_module_accesable = (username, modulename) => {
    if (this.state.data)
      if (this.state.data[username])
        if (this.state.data[username][modulename])
          return this.state.data[username][modulename]
        else return false
  }

  get_assigned_roles_row = (username) => {
    let result = [
      <td>
        {get_locales(username)}
      </td>
    ]
    let available_modules = ['captain', 'navigator', 'cannoneer', 'engineer']
    for (let i in available_modules) {
      let modulename = available_modules[i]
      result.push(<td>
        <td><input type='checkbox' disabled={((modulename === username)&&(this.props.username!=="admin"))} onClick={(e) => {

          this.onAssignRole(username, modulename, e.target.checked)
        }} checked={this.is_module_accesable(username, modulename)} /></td>
      </td>)
    }
    return <tr>{result}</tr>
  }

  get_roles_table = () => {
    let result = []
    let usernames = ["captain", "navigator", "cannoneer", "engineer"]
    for (let i in usernames) {
      let username = usernames[i]
      result.push(this.get_assigned_roles_row(username))
    }
    return <table>
      <thead>
        <th>{get_locales("")}</th>
        <th>{get_locales("captain")}</th>
        <th>{get_locales("navigator")}</th>
        <th>{get_locales("cannoneer")}</th>
        <th>{get_locales("engineer")}</th>
      </thead>
      <tbody>
        {result}
      </tbody>
    </table>
  }

  render() {
    return <div>
      {this.get_roles_table()}
    </div>
  }
}
