import React from 'react'
import { get_ships_state, send_command } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';




export class ShipsStateWidget extends React.Component {
 constructor(props) {
  super(props);


  this.state = {
   data: {},
   hided: false,
   ships_state: {}
  }
 }

 componentDidMount() {
  this.take_control(null)
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

 take_control = (key) => {
  send_command("connection", key, "take_control_on_entity", { 'target_id': key })
  this.props.on_ship_selected(key)
  if (key) this.props.on_module_selection("pilot")
 }

 proceed_data_message = () => {
  this.setState({ "ships_state": get_ships_state() })
 }

 get_ship_widget = (key, descr) => {
  let result = [<button onClick={(e) => { this.take_control(key) }}><b>{key}</b></button>]
  for (let k in descr) {
   result.push(
    <label>{k}: {descr[k]}</label>
   )
  }
  return <div className='AdminShipStateWidget'>{result}</div>
 }

 get_ship_widgets_list = () => {
  let result = []
  for (let k in this.state.ships_state) {
   result.push(
    this.get_ship_widget(k, this.state.ships_state[k])
   )
  }
  return <div className='ShipsSection'>{result}</div>
 }

 render() {



  return (
   <div className='ShipStateViewer'>
    <label onClick={() => { this.setState({ hided: !this.state.hided }); }}><b>SHIPS STATE</b></label>
    {this.get_ship_widgets_list()}
   </div>
  )
 }

}
