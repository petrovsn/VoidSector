
import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';

export class HospitalCrewWidget extends React.Component {
 constructor(props) {
  super(props);




  
  this.state = {
  data: {

  },
  hided: true,
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
  let med_data = get_system_state( "med_sm")
  if (med_data) this.setState({ "data": med_data })
 }



  



  
 render() {
  let data = <span></span>
  if (this.state.data){
  data = <label>{this.state.data.units}/{this.state.data.capacity}</label>
  }
  return (
  <div
   className='SystemControlWidget'>
   <b>Hospital Crew Control</b>
   {data}
  </div>
  )
 }



  
 }
