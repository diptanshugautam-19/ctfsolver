package com.kakashi.sharingan_jutsu.controller;

import org.apache.commons.text.StringSubstitutor;
import org.apache.commons.text.lookup.StringLookupFactory;
import org.springframework.web.bind.annotation.*;

@RestController
public class KakashiSenseiController {
    
    @RequestMapping(value = "/", method = RequestMethod.GET)
    @ResponseBody
    public String index() {
        StringBuilder sb = new StringBuilder();

    sb.append("<!doctype html>");
    sb.append("<html lang=\"en\">");
    sb.append("<head>");
    sb.append("<meta charset=\"utf-8\"/>");
    sb.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>");
    // Inline CSS - centered layout
    sb.append("<style>");
    sb.append("  body { display:flex; align-items:center; justify-content:center; min-height:100vh; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; background:#0f1724; color:#e6eef8; margin:0; padding:20px; }");
    sb.append("  .wrap { width:100%; max-width:900px; background:linear-gradient(135deg,#0b1220 0,#0f1b2b 100%); border-radius:12px; box-shadow:0 8px 30px rgba(2,6,23,0.6); padding:28px; }");
    sb.append("  h1 { margin:0 0 8px 0; font-size:28px; color:#f8fafc; text-align:center; }");
    sb.append("  p.lead { margin:6px 0 20px 0; color:#c9d6e6; text-align:center; }");
    sb.append("  .kbd { display:inline-block; background:#071428; border:1px solid rgba(255,255,255,0.04); padding:6px 8px; border-radius:6px; font-family:monospace; }");
    sb.append("  .card { background:rgba(255,255,255,0.02); padding:14px; border-radius:8px; margin-bottom:12px; }");
    sb.append("  a.btn { display:inline-block; background:#2b6cb0; color:white; padding:10px 14px; border-radius:8px; text-decoration:none; margin-right:8px; }");
    sb.append("  a.btn:hover{ background:#2c5282; }");
    sb.append("  .warn { color:#ffd7a6; font-weight:600; }");
    sb.append("  footer { font-size:12px; color:#94a3b8; margin-top:18px; text-align:center; }");
    sb.append("</style>");
    sb.append("<title>Kakashi Jutsu</title>");
    sb.append("</head>");
    sb.append("<body>");
    sb.append("<div class=\"wrap\">");
    sb.append("<h1>🌀 Kakashi Is Here</h1>");
    sb.append("<p class=\"lead\">Kakashi will copy your jutsu exactly. Is he in your mind?</p>");

    sb.append("<div class=\"card\">");
    sb.append("<strong>Try It!</strong>");
    sb.append("<ou>");
    sb.append("<li>Send Your Chakra here: ");
    sb.append("<code class=\"kbd\">/copyninja?chakra=</code></li>");
    sb.append("</ul>");
    sb.append("</div>");

    sb.append("</div>"); // wrap
    sb.append("</body>");
    sb.append("</html>");

        return sb.toString();
    }

    @RequestMapping(value = "/copyninja", method = RequestMethod.GET)
    @ResponseBody
    public String copyninja(@RequestParam(name = "chakra", defaultValue = "") String kakashi_poc) {
        StringSubstitutor kakashi_interpolator = new StringSubstitutor(StringLookupFactory.INSTANCE.interpolatorStringLookup());
        try {
            String vuln = kakashi_interpolator.replace(kakashi_poc);
        } catch (Exception chakra_exception) {
            System.out.println(chakra_exception);
        }
        return "Result: " + kakashi_poc;
}
}
