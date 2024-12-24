import React from 'react'
import { get_performance, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';

const average = arr => arr.reduce((p, c) => p + c, 0) / arr.length;
class Smoother {
 constructor() {
  this.maxLen = 30
  this.raw_data = {}
  this.frontfps_array = []
  this.last_timestamp = Date.now()
 }

 add_data = (key, value) => {
  if (!(key in this.raw_data)) this.raw_data[key] = []
  this.raw_data[key].push(value)
  if (this.raw_data[key].length > this.maxLen) this.raw_data[key] = this.raw_data[key].slice(1)
 }

 add_timestamp = () => {
  let t = Date.now()
  let dt = t - this.last_timestamp
  if (dt === 0) return

  this.add_data("FPS", 1000/dt)
  this.last_timestamp = Date.now()
 }

 get_last_values = () => {
  let result = {}
  for (let k in this.raw_data) {
   result[k] = this.raw_data[k][this.raw_data[k].length - 1]
  }
  return result
 }

 get_avg_stats = () => {

  let result = {}
  for (let k in this.raw_data) {
   result[k] = average(this.raw_data[k]).toFixed(2)
  }
  return result
 }

 get_persec_stats = () => {
  let result = {}
  for (let k in this.raw_data) {
   result[k] = (1000 / average(this.raw_data[k])).toFixed(2)
  }
  return result
 }
}

const smoother = new Smoother()

export class PerformanceViewer extends React.Component {
 constructor(props) {
  super(props);

  this.state = {
   data: {},
   hided: false,
   system_state: {}
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
  let perf_data = get_performance()
  this.setState({ "data": perf_data })
  for (let k in perf_data) {
   smoother.add_data(k, perf_data[k])
  }
  smoother.add_timestamp()
  this.setState({"system_state":get_system_state})
 }

 render() {
  let stats = []
  if (!this.state.hided) {
   let last_vals = smoother.get_last_values()
   //let avg_stats = smoother.get_avg_stats()
   //let persec_stats = smoother.get_persec_stats()

   for (let k in last_vals) {
    stats.push(<label> {k}: {last_vals[k].toFixed(4)}</label>)
    //stats.push(<label> {k}(Avg): {avg_stats[k]}</label>)
    //stats.push(<label> {k}(PSc): {persec_stats[k]}</label>)
   }
  }

  return (<div className='AdminSystemViewer'>
   <label onClick={()=>{this.setState({hided:!this.state.hided});}}><b>PERFORMANCE</b></label>
   {stats}
  </div>)
 }
}
