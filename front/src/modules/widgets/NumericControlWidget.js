
import React from 'react'
import '../../styles/NumericControlWidget.css'
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';
export class NumericControlWidjet extends React.Component {
 constructor(props) {
  super(props);
  this.state = {
   "value": this.props.init_value
  }
 }
 onChange = (e) => {
  this.setState({ "value": e.target.value }, this.props.onChange(parseFloat(this.state.value)))
 }
 render() {
  return (<label>{get_locales(this.props.label)}:<input
   disabled={this.props.disabled}
   type="range"
   min={this.props.min}
   max={this.props.max}
   step={this.props.step}
   class="slider"
   value={this.state.value}
   onChange={this.onChange}
  //value={this.state.progradeAcc}
  />
   {parseFloat(this.state.value).toFixed(2)}
  </label>
  )
 }
}


export class NumericStepControlWidjet extends React.Component {
 constructor(props) {
  super(props);
  this.state = {
   "value": this.props.init_value,
   "step": 0,
  }
 }

 componentDidMount() {
  let timer_id = timerscounter.get(this.constructor.name)
  if (!timer_id) {
   clearInterval(timer_id)
  }
  timer_id = setInterval(this.step, 30)
  timerscounter.add(this.constructor.name, timer_id)
 }

 componentWillUnmount() {
  let timer_id = timerscounter.get(this.constructor.name)
  clearInterval(timer_id)
 }

 step = () => {
  let value = this.state.value + this.state.step
  if (value< this.props.min) value = value%this.props.max
  if (value > this.props.max) value = value%this.props.max
  if (value !== this.state.value) {
   this.setState({ "value": value }, this.props.onChange(value))
  }
 }

 onChange = (e) => {
  this.setState({ "value": e.target.value })
 }

 onChangeStep = (value) => {
  this.setState({ "step": value })
 }

 render() {
  //console.log("NumericStepControlWidjet")
  return (
   <div className='NumericStepControlWidjet'>
    <label>{get_locales(this.props.label)}</label>
    <button
     onMouseDown={(e) => { this.onChangeStep(-this.props.step) }}
     onMouseUp={(e) => { this.onChangeStep(0) }}
     onMouseLeave={(e) => { this.onChangeStep(0) }}
    >{"<<"}</button>

    <button
     onMouseDown={(e) => { this.onChangeStep(this.props.step) }}
     onMouseUp={(e) => { this.onChangeStep(0) }}
     onMouseLeave={(e) => { this.onChangeStep(0) }}
    >{">>"}</button>
    <label className='value_label'>{parseFloat(this.state.value).toFixed(2)}</label>

   </div>
  )
 }
}
