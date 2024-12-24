import React from 'react'
import { get_capmarks, get_observer_id, send_command } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';

export class CapMarksControlWidget extends React.Component {
 constructor(props) {
  super(props);


  this.state = {
   data: {
   },
  }
 }

 componentDidMount() {
  let timer_id = timerscounter.get(this.constructor.name)
  if (!timer_id) {
   clearInterval(timer_id)
  }
  timer_id = setInterval(this.proceed_data_message, 30)
  timerscounter.add(this.constructor.name, timer_id)
 }

 componentWillUnmount() {
  let timer_id = timerscounter.get(this.constructor.name)
  clearInterval(timer_id)
 }

 proceed_data_message = () => {
  let data = get_capmarks("radar_sm")
  let mark_id = get_observer_id()
  if (data) this.setState({ "data": data, "mark_id": mark_id })
 }

 onSelect = (char) => {
  send_command("ship.cap_marks", this.state.mark_id, "select_point", { "char": char })
 }

 onDeactivate = (char) => {
  send_command("ship.cap_marks", this.state.mark_id, "deactivate_point", { "char": char })
 }

 get_capmark_control = (char) => {
  return <tr>
   <td>
    {char}
   </td>
   <td>
    {this.state.data[char]["position"][0]}, {this.state.data[char]["position"][1]}
   </td>
   <td>
    {this.state.data[char]["active"] ? "true" : "false"}
   </td>
   <td>
    <button onClick={(e) => { this.onSelect(char) }}>{get_locales("select")}</button>
   </td>
   <td>
    <button onClick={(e) => { this.onDeactivate(char) }}>{get_locales("deaсtivate")}</button>
   </td>
  </tr>
 }

 get_capmarks_table = () => {
  let result = []
  for (let char in this.state.data) {
   result.push(this.get_capmark_control(char))
  }
  return (
   <table>
    <thead>
     <th>{get_locales("MarkLetter")}</th>
     <th>{get_locales("Position")}</th>
     <th>{get_locales("Status")}</th>

    </thead>
    <tbody>
     {result}
    </tbody>
   </table>
  )
 }


 render() {
  return (
   <div className='SystemControlWidget'>
    <b>{get_locales("CapPointsController")}</b>
    {this.get_capmarks_table()}
   </div>
  )
 }

}
