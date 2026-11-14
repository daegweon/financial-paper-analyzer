import {createClient,type SupabaseClient} from "@supabase/supabase-js";
let client: SupabaseClient|null=null;
export function db(): SupabaseClient {const url=process.env.NEXT_PUBLIC_SUPABASE_URL; const key=process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY; if(!url||!key) throw new Error("Supabase 환경변수가 없습니다."); if(!client) client=createClient(url,key,{auth:{persistSession:true,autoRefreshToken:true,flowType:"pkce",detectSessionInUrl:true}}); return client;}
