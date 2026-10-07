export const PROJECT_META = { 
  teamName: "", 
  members: ["Nizma Najeeb","Devika K.S","Anjana Priya A.P","Adhya P.A"], 
  college: "Christ College of Engineering, Irinjalakuda (Autonomous)" 
};

export const NAV_ITEMS = [
  {to:"/",label:"Dashboard",icon:"LayoutDashboard"},
  {to:"/analyze",label:"Analyze",icon:"FileSearch"},
  {to:"/profile",label:"Trust Profile",icon:"UserCheck"},
  {to:"/history",label:"History",icon:"History"},
  {to:"/how-it-works",label:"How It Works",icon:"BookOpen"}
];

export const DECISION_META = { 
  ALLOW: {color:"var(--allow-text)",label:"ALLOW"}, 
  VERIFY: {color:"var(--verify-text)",label:"VERIFY"}, 
  BLOCK: {color:"var(--block-text)",label:"BLOCK"} 
};

export const SOURCE_META = { 
  measured: {label:"MEASURED",hint:"Computed by real code on an uploaded file. An indicator, not proof."}, 
  user_supplied: {label:"USER-SUPPLIED",hint:"Entered or toggled by the operator."}, 
  simulated: {label:"SIMULATED",hint:"Preset demo value. No real detection was performed."},
  profile: {label:"PROFILE",hint:"Compared against the stored trust profile."}
};

export const HEALTH_POLL_MS = 10000;
