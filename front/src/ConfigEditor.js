
import React from 'react'

import { send_command, get_http_address } from './modules/network/connections.js'

import { timerscounter } from './modules/utils/updatetimers.js';


import './styles/Administration.css'
import './styles/ConfigEditor.css'



export class ConfigEditor extends React.Component {
 constructor(props) {
 super(props);
 this.state = {
  config_list: [],
  config_data: {},
  configfile_name:""
 }
 }

 componentDidMount() {
 let timer_id = timerscounter.get("ConfigEditor")

 if (!timer_id) {
  //clearInterval(timer_id)
 }



  
  timer_id = setInterval(this.updateConfigList, 1000)
  timerscounter.add("ConfigEditor", timer_id)
  this.updateConfigList()
 }

 componentWillUnmount() {



  
 let timer_id = timerscounter.get("ConfigEditor")

 clearInterval(timer_id)
 }

 updateConfigList = () => {
 var myInit = {
  method: "GET",
  headers: {
  },
 }

 return fetch(get_http_address() + "/admin/configs", myInit)
  .then(response => {
  let code = response.status;

  switch (code) {
   case 200:
   let data = response.json()
   return data
   default:
   break;
  }
  })
  .then(data => {

  this.setState({
   config_list: data
  })
  })
  .catch(error => {

  });
 }


 getConfig = (filename) =>{
 var myInit = {
  method: "GET",
  headers: {
  },
 }

 return fetch(get_http_address() + "/admin/configs/"+filename, myInit)
  .then(response => {
  let code = response.status;

  switch (code) {
   case 200:
   let data = response.json()
   return data
   default:
   break;
  }
  })
  .then(data => {

  this.setState({
   configfile_name: filename.split('.')[0],
   config_data: data
  })
  })
  .catch(error => {

  });
 }

 get_configs_list = () => {
 let result = []
 for (let i in this.state.config_list) {
  let conf = this.state.config_list[i]
  result.push(
  <label onClick={() => { 
   this.getConfig(conf)
   send_command("config_loader", "admin", "load", { "filename": conf })
   }} >{conf}</label>
  )
 }
 return <div className='map_selector'>{result} </div>
 }

 onSaveCurrent = () => {
 send_command("config_loader", "admin", "save", { "filename": this.state.configfile_name, "config_data":this.state.config_data })
 //send_command("config_loader", "admin", "load", { "filename": this.state.configfile_name })
 }



 get_config_list = () => {
 return (<div
  className='FileLoader'
 >
  <b>ConfigLoader</b>
  {this.get_configs_list()}

  <input onChange={(e) => { this.setState({ "configfile_name": e.target.value }) }} value={this.state.configfile_name}></input>
  <button onClick={this.onSaveCurrent}>SAVE</button>
 </div>)
 }

 get_config_content = () =>{
 let result = []
 for(let section_name in this.state.config_data){
  result.push(this.get_config_section(section_name))
 }
 return <div className = "configContent"> {result} </div>
 }

 change_option = (section_name, param_name, value) =>{
 let tmp_config = this.state.config_data
 tmp_config[section_name][param_name] = value
 this.setState({"config_data":tmp_config})
 }

 get_config_section = (section_name) =>{
 let result = []
 for (let label in this.state.config_data[section_name]){
  result.push(<label>{label}<input onChange={(e)=>{this.change_option(section_name, label, e.target.value)}} value={this.state.config_data[section_name][label]}></input></label>)
 }
 return <div className='configSection'>
  <label><b>{section_name}</b></label>
  {result}
 </div>
 }

 render() {
 return (<div
  className='ConfigEditor'
 >
  {this.get_config_list()}
  {this.get_config_content()}

 </div>)
 }
}
