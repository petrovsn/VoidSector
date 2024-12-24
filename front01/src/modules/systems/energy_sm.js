
import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';

export class EnergyControlWidget extends React.Component {
 constructor(props) {
 super(props);


 this.state = {
  data: {
  systems_energy: {}
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
 let perf_data = get_system_state("energy_sm")
 if (perf_data) this.setState({ "data": perf_data })
 }

 onIncreaseEnergy = (system_name) => {
 send_command("ship.energy_sm", this.state.data.mark_id, "increase_energy_level", { "system": system_name })
 }

 onDecreaseEnergy = (system_name) => {
 send_command("ship.energy_sm", this.state.data.mark_id, "decrease_energy_level", { "system": system_name })
 }


 get_energy_limit = () => {
 let result = [<button disabled>{">>"}</button>]
 let free_energy = this.state.data.energy_free
 for (let i = 0; i < free_energy; i++) {
  result.push(<button className='back_green' disabled> {i + 1} </button>)
 }
 return <div className="systemUpgradeUnit">{result}</div>
 }

 get_energy_controls = () => {
 let result = []
 for (let system_name in this.state.data.systems_energy) {
  let energy_level = this.state.data.systems_energy[system_name]
  let level_widgets = []


  level_widgets.push(<button onClick={(e) => { this.onDecreaseEnergy(system_name) }}>
  -
  </button>)

  for (let i = 0; i < Number.parseInt(energy_level); i++) {
  let classname = ""
  if (i >= 4) classname = 'back_red'
  level_widgets.push(<button className={classname} disabled> {i + 1} </button>)
  }

  level_widgets.push(<button onClick={(e) => { this.onIncreaseEnergy(system_name) }}>
  +
  </button>)


  result.push(
  <div className="systemUpgradeUnit">
   <label>{get_locales(system_name)}</label>
   <div>
   {level_widgets}

   </div>
  </div>
  )
 }

 return result
 }

 render() {
 return (
  <div
  className='SystemControlWidget'>
  <b>{get_locales("Energy control")}</b>
  {this.get_energy_limit()}
  {this.get_energy_controls()}
  </div>
 )
 }

}
