
import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { get_locales } from '../locales/locales';
import { timerscounter } from '../utils/updatetimers';



export class ResourcesControlWidget extends React.Component {
 constructor(props) {
 super(props);


 this.state = {
  data: {},
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
 let perf_data = get_system_state("resources_sm")
 this.setState({ "data": perf_data })
 }

 cancel_item = (e) => {
 send_command("ship.resources_sm", this.state.data.mark_id, "cancel_item_production", {})
 }

 clear_production = (e) => {
 send_command("ship.resources_sm", this.state.data.mark_id, "clear_production", {})
 }

 remove_item_from_queue = (item_name, item_idx) =>{
 send_command("ship.resources_sm", this.state.data.mark_id, "remove_item_from_production_queue", {"item_name":item_name, "item_idx":item_idx})
 }

 get_resource_header = () => {
 let result = []
 for (let res_name in this.state.data.stockpile_raw) {
  result.push(<label>{get_locales(res_name)}($): {this.state.data.stockpile_raw[res_name].toFixed(2)}/{this.state.data.stockpile_raw_capacity}</label>)
 }
 result.push(<label>{get_locales("volume")}(◪): {this.state.data.stockpile_items_occupied}/{this.state.data.stockpile_items_capacity}</label>)
 return <div className='StockpileRaw'>
  {result}
 </div>
 }

 produce = (item_name) => {
 send_command("ship.resources_sm", this.state.data.mark_id, "produce_item", { "item_name": item_name })
 }

 get_items = () => {
 let render_array = []
 if (this.state.data) {
  for (let k in this.state.data.stockpile_items) {
  let cost = this.state.data.items_cost[k]
  let volume = this.state.data.items_volume[k]
  render_array.push(<label><button onClick={() => { this.produce(k) }}>{k} [{this.state.data.stockpile_items[k]}]</button>: ${cost} ◪{volume}</label>)
  }
 }
 return <div className='StockpileItems'>
  {render_array}
 </div>
 }

 get_production_queue = () => {
 let render_array = []
 if (this.state.data) {
  for (let i in this.state.data.production_queue) {
  let item = this.state.data.production_queue[i]
  let item_name = item[0]
  let item_count = item[1]
  render_array.push(<button onClick={() => {this.remove_item_from_queue(item_name, i) }}>{item_name} [{item_count}]</button>)
  }
 }
 return <div className='ProductionQueueSection'>
  <div className='productionQueue'>
  {render_array}
  </div>
  <button onClick={this.clear_production}>{get_locales("clear_production")}</button>
 </div>
 }

 get_production_progress = () => {
 return (
  <div className={"labeled_progress_bar"}>
  <label>{this.state.data.production_task}</label>
  <progress value={this.state.data.production_progress} max="1"></progress>
  <button onClick={this.cancel_item}> {get_locales("cancel_item")} </button>
  </div>)
 }

 render() {
 if (!this.state.data) return (<div className='SystemControlWidget'> <label><b>{get_locales("Production_sm")}</b></label></div>)
 let render_array = []
 if (this.state.data) {
  for (let k in this.state.data.stockpile_raw) {
  render_array.push(<label>{k}: {this.state.data.stockpile_raw[k]}</label>)
  }
 }
 return (

  <div className='SystemControlWidget ProductionSM'>
  <label><b>{get_locales("Production_sm")}</b></label>

  {this.get_resource_header()}
  <div className="items_section">
   {this.get_items()}
   {this.get_production_queue()}
  </div>

  {this.get_production_progress()}
  </div>
 )
 }

}
