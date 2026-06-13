# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_image_options_only_verbose_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 81 | 42.4% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 40 | 34.8% |
| `relative_position` | 76 | 76 | 41 | 53.9% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 45 | 53.6% |
| 4 | 107 | 107 | 36 | 33.6% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 1 | `direct_attributes` | C | A | `Looking at the image, we can see a flower shop with various flowers displayed outside. Among them, there are prominent c` |
| 3 | `direct_attributes` | B | A | `The image shows a section of the Berlin Wall, which is primarily made of concrete. The dominant color of the wall itself` |
| 4 | `direct_attributes` | C | A | `The image shows a group of people in what appears to be a greenhouse or flower exhibition, surrounded by rows of colorfu` |
| 8 | `direct_attributes` | B | A | `The image shows a scenic canal in what appears to be a traditional Chinese water town. The buildings on the right have w` |
| 9 | `direct_attributes` | D | B | `The image shows a large truck, specifically the cab of a MAN truck. The main body of the truck cab is clearly white. Whi` |
| 12 | `direct_attributes` | C | D | `Looking at the image, we can see a wooden boat surrounded by green aquatic plants. There are two people visible:  - One ` |
| 15 | `direct_attributes` | D | B | `The image shows the exterior of a building with a glass facade. The glass reflects the sky and surrounding environment, ` |
| 16 | `direct_attributes` | B | A | `The image shows a memorial complex with several elements. The most prominent features are:  - Two tall, light-colored (l` |
| 17 | `direct_attributes` | D | C | `Looking at the image, we can see several cars parked along the street at night. The question is likely asking about the ` |
| 18 | `direct_attributes` | C | D | `The image shows several boats in what appears to be a floating market, likely in Southeast Asia. The boats are tradition` |
| 19 | `direct_attributes` | A | C | `The image shows a street scene with buildings, shops, and a bicycle in the foreground. The bicycle is prominently displa` |
| 22 | `direct_attributes` | C | D | `The image shows a man walking on a golf course pulling a golf bag on a cart. The golf bag is primarily **blue**, with so` |
| 24 | `direct_attributes` | B | A | `The image shows a large river cruise ship docked at a pier. The main body of the ship is predominantly white, with some ` |
| 26 | `direct_attributes` | B | A | `The question asks to choose a color from the options: (A) blue, (B) yellow, (C) green, (D) red — based on the image.  Lo` |
| 28 | `direct_attributes` | C | B | `The image shows a large brick building with white columns and a tall steeple. The main body of the building is construct` |
| 29 | `direct_attributes` | B | D | `The image prominently features a large swimming pool in the foreground. The water in the pool is clearly blue, and the t` |
| 31 | `direct_attributes` | C | D | `The image shows a street scene with buildings, cars, and trees under a clear sky. The most dominant color in the upper p` |
| 33 | `direct_attributes` | C | D | `The image shows a lush landscape dominated by greenery — vineyards in the foreground, trees, and forested hills in the b` |
| 35 | `direct_attributes` | C | D | `The image shows a coastal scene with cliffs, beach, and ocean. The question does not specify what object or feature the ` |
| 38 | `direct_attributes` | B | A | `Looking at the image, we can see a cobblestone street with painted lines. In the foreground, there is a yellow line pain` |
| 39 | `direct_attributes` | C | A | `The image depicts a winter scene with frost-covered trees and patches of snow on the ground and sidewalk. The dominant c` |
| 40 | `direct_attributes` | B | A | `The image shows an outdoor market scene with several tents and stalls. In the foreground, there are tree branches with b` |
| 41 | `direct_attributes` | C | A | `The image shows a city street scene with a large pile of trash bags on the sidewalk next to a black ornate lamppost. The` |
| 42 | `direct_attributes` | A | B | `The image shows a scenic view of Cologne, Germany, with the famous Cologne Cathedral in the background. In the foregroun` |
| 44 | `direct_attributes` | D | A | `The image shows a dental office with various pieces of furniture and equipment. Notably, several items are colored green` |
| 45 | `direct_attributes` | D | A | `The image shows a modern building with a facade that includes sections of glass and what appears to be stone or concrete` |
| 46 | `direct_attributes` | A | B | `The image shows a resort-like setting with buildings, palm trees, and green grass under a clear sky. The most prominent ` |
| 47 | `direct_attributes` | A | C | `Looking at the image, we can see a large sign for “First Canadian Place” at the top. The text “First Canadian Place” is ` |
| 48 | `direct_attributes` | B | A | `The image shows several beach chairs (Strandkörbe) on a sandy beach. The main body of these chairs is made of white wick` |
| 49 | `direct_attributes` | C | D | `The image shows a large building decorated for Christmas, with prominent red elements: red awnings, red banners reading ` |
| 50 | `direct_attributes` | A | C | `The image shows a city scene with a pedestrian overpass. The stairs leading up to the overpass are made of reddish-brown` |
| 51 | `direct_attributes` | A | D | `The image shows a riverboat with a predominantly white hull and blue trim, including blue railings, blue accents along t` |
| 53 | `direct_attributes` | C | D | `The image shows a large traditional Japanese temple building, likely Senso-ji in Tokyo. The main structure has prominent` |
| 54 | `direct_attributes` | A | B | `The image shows a park scene with lush green grass in the foreground, green trees on both sides, and manicured green hed` |
| 55 | `direct_attributes` | D | A | `The image shows a charming alleyway in what appears to be a Greek island town (likely Mykonos or similar), characterized` |
| 56 | `direct_attributes` | A | D | `Looking at the image, we can see a busy urban street scene with buildings, cars, pedestrians, and traffic signals.  In t` |
| 58 | `direct_attributes` | B | A | `The image shows a large floral clock on a grassy hill, flanked by two cartoon-like figures made of flowers. The figure o` |
| 59 | `direct_attributes` | A | D | `Looking at the image:  - The sky is a vivid **blue**. - The large building on the right has a glass facade that reflects` |
| 61 | `direct_attributes` | A | C | `The question appears to be asking for the color of a specific object or person in the image, but since no explicit subje` |
| 62 | `direct_attributes` | D | B | `The image shows a large building complex with prominent red roofs. The question likely refers to the most noticeable or ` |
| 63 | `direct_attributes` | D | C | `Looking at the image, we can see a person pushing a stroller with a child inside. The child is wearing a bright red jack` |
| 64 | `direct_attributes` | A | B | `Looking at the image, we can see several people in the background. The woman walking on the sidewalk (to the right of th` |
| 65 | `direct_attributes` | A | B | `The image shows a decorative bicycle sculpture in a garden. The frame of the bicycle — specifically the part connecting ` |
| 66 | `direct_attributes` | B | A | `The image shows a public plaza with trees, buildings, and a small kiosk. The kiosk has colorful elements — orange base, ` |
| 67 | `direct_attributes` | B | C | `The image shows a snowy winter scene with two vehicles: an ATV in the foreground and a tracked utility vehicle ahead. Th` |
| 68 | `direct_attributes` | A | B | `The image shows a waterfront scene with several buildings. In the foreground, floating on the water, is a large barge or` |
| 69 | `direct_attributes` | C | B | `The image shows an empty children’s playroom with toys, a plastic playhouse, wall decorations (including cartoon rabbits` |
| 70 | `direct_attributes` | B | A | `The image shows an archaeological site with excavated foundations in the foreground. These foundations are made of stone` |
| 71 | `direct_attributes` | B | D | `The image shows a beach scene with a prominent red marker or buoy on a pole extending into the water. This red object st` |
| 72 | `direct_attributes` | C | A | `Looking at the image, we see a forest of tall pine trees with various painted symbols on their trunks — mostly eyes and ` |
| 73 | `direct_attributes` | B | A | `The image shows a street food vendor on a beach. The cart he is using is painted blue — you can see the blue paint on th` |
| 74 | `direct_attributes` | A | C | `Looking at the image, we can see three flags on flagpoles to the left of the gate:  - The leftmost flag is yellow. - The` |
| 77 | `direct_attributes` | C | B | `The image shows a cobblestone town square with half-timbered buildings under a bright blue sky. The most dominant and ex` |
| 78 | `direct_attributes` | C | A | `The image shows an elephant interacting with people at what appears to be a fair or outdoor event. The elephant’s skin i` |
| 81 | `direct_attributes` | A | D | `The most prominent and defining feature of the building in the image is its large, curved roof. This roof is constructed` |
| 83 | `direct_attributes` | D | A | `The image shows a historic building with stone walls that are predominantly light in color — specifically, they appear t` |
| 84 | `direct_attributes` | A | B | `Looking at the image, we can see a narrow street lined with colorful shophouses. On the left side, there is a prominent ` |
| 86 | `direct_attributes` | A | C | `The image shows a large, stately building with a prominent facade. The main color of the building’s exterior walls is a ` |
| 87 | `direct_attributes` | B | A | `The image shows a large war memorial with bronze sculptures of soldiers and horses. The bronze material has oxidized ove` |
| 89 | `direct_attributes` | D | B | `The image shows a cityscape with the Oriental Pearl Tower and modern skyscrapers. In the foreground, there is a road wit` |
| 90 | `direct_attributes` | C | A | `The image shows a highway scene with several vehicles. The most prominent vehicle in the foreground is an SUV, which is ` |
| 91 | `direct_attributes` | B | D | `The image shows a group of people at what appears to be an outdoor shooting range. Most individuals are wearing dark clo` |
| 95 | `direct_attributes` | A | B | `The image shows a street scene with white-washed buildings that have prominent blue accents — particularly on the lower ` |
| 96 | `direct_attributes` | C | A | `The image shows a large collection of hats, mostly straw hats in natural beige or tan colors. However, looking closely a` |
| 99 | `direct_attributes` | D | C | `The image shows a beach scene with thatched umbrellas in the foreground. These umbrellas are made of dried plant materia` |
| 100 | `direct_attributes` | C | B | `The image shows a large, ornate building with a prominent roof. The roof is clearly visible and is colored red. While th` |
| 101 | `direct_attributes` | B | A | `The image shows a scenic view of a town built on a hillside next to a body of water. The dominant colors in the scene ar` |
| 102 | `direct_attributes` | C | B | `The house in the image has white siding, white trim, and a white garage door. While there are black accents (window fram` |
| 103 | `direct_attributes` | B | D | `The image prominently features a large, bright red post box in the foreground. The word “POS” is embossed on it, and it ` |
| 104 | `direct_attributes` | B | C | `The image shows a beach scene with ocean water in the foreground. The water is clearly blue, with varying shades due to ` |
| 105 | `direct_attributes` | D | A | `The image shows a library interior with prominent green-shaded lamps on wooden desks. The question asks to choose from c` |
| 106 | `direct_attributes` | A | D | `The question appears to be asking for the color of an item in the image — likely the flowers held by the woman on the le` |
| 107 | `direct_attributes` | A | C | `The image shows a modern furniture display with a large sofa as the central piece. The sofa is upholstered in a warm, ea` |
| 108 | `direct_attributes` | D | C | `The image shows a resort pool area with palm trees, lounge chairs, and people enjoying the water. The question asks to c` |
| 112 | `direct_attributes` | D | A | `The image shows a European-style town square with cobblestone pavement, historic buildings, and people walking. The sky ` |
| 120 | `relative_position` | B | A | `The image shows a park scene with a pond in the foreground. On the left side of the pond, there is a small wooden viewin` |
| 122 | `relative_position` | B | A | `The image shows a church with a tall bell tower and a large building facade on the left, set against a bright blue sky. ` |
| 128 | `relative_position` | B | A | `The image shows a street scene with a large stone archway in the center. To the left of the archway, there is a row of b` |
| 129 | `relative_position` | B | A | `The image shows a large stone arch monument (Wellington Arch) in the center. To the right of the arch, there is a traffi` |
| 130 | `relative_position` | B | A | `The image shows two people paddleboarding on a calm body of water. The person on the **left** is wearing red shorts and ` |
| 131 | `relative_position` | B | A | `The image shows a train station platform with a yellow and red S-Bahn train on the left side of the frame. The platform ` |
| 132 | `relative_position` | B | A | `The image shows a youth soccer game in progress. The goal visible in the foreground is on the **left** side of the image` |
| 133 | `relative_position` | B | A | `The image shows a street scene in Paris, with the Hôtel de Ville (City Hall) prominently featured in the background. In ` |
| 135 | `relative_position` | B | A | `The question is ambiguous without a specific reference point (e.g., “Which side is the blue boat on?” or “Which side has` |
| 136 | `relative_position` | B | A | `The image shows a canal scene, likely in Amsterdam. On the **left side** of the canal, there is a row of parked cars, bi` |
| 137 | `relative_position` | A | B | `The image shows a cobblestone street with buildings lining the right side. The perspective of the photo is such that the` |
| 141 | `relative_position` | A | B | `The image shows a grand building with classical architecture, likely the Luxembourg Palace in Paris, viewed from its gar` |
| 142 | `relative_position` | B | A | `The question is ambiguous without a specific prompt (e.g., “Which side is the blue boat on?” or “Which side has the rust` |
| 143 | `relative_position` | A | B | `The image shows a resort scene with palm trees, pools, and the ocean. The question asks to choose between “left” or “rig` |
| 144 | `relative_position` | B | A | `The image shows a street intersection with traffic lights, pedestrians, and vehicles. The question is simply “(A) right ` |
| 148 | `relative_position` | B | A | `The image shows a small house with a yard. On the **left side** of the image, we can see:  - A window with decorative me` |
| 149 | `relative_position` | B | A | `The image shows a street scene with two main structures:  - On the **left side**, there is a traditional Lao-style templ` |
| 151 | `relative_position` | B | A | `The image shows a wide, tree-lined street with vehicles and cyclists. On the **left side** of the road (from the viewer’` |
| 157 | `relative_position` | B | A | `The image shows a wide beach scene. On the **left side**, there are two prominent tall glass skyscrapers, along with som` |
| 158 | `relative_position` | B | A | `The image shows a street scene with buildings lining the left side of the frame. The HSBC UK bank is prominently on the ` |
| 161 | `relative_position` | A | B | `The image shows a wide cobblestone plaza with classical architecture. On the right side of the image, there is a promine` |
| 162 | `relative_position` | B | A | `The image shows a historic stone castle or fortress situated on a hill, with trees surrounding it. In the foreground, th` |
| 163 | `relative_position` | B | A | `The question is ambiguous without context — it doesn’t specify what “right” or “left” refers to. However, in visual mult` |
| 165 | `relative_position` | B | A | `The image shows an outdoor market scene with clothing stalls. The main red tent and most of the merchandise are position` |
| 167 | `relative_position` | B | A | `The image shows a street scene with pedestrians walking on the sidewalk. In the foreground, a group of three people (an ` |
| 168 | `relative_position` | B | A | `The image shows a street scene with buildings, vehicles, and people. The question asks to choose between “left” or “righ` |
| 172 | `relative_position` | A | B | `The image shows a lake scene with a person standing on a paddleboard in the center of the water, performing a yoga pose ` |
| 173 | `relative_position` | B | A | `The image shows a cobblestone courtyard with large stone pillars and arches. On the **left side**, there is a dark statu` |
| 175 | `relative_position` | B | A | `The image shows a beach scene with the ocean and horizon extending toward the right side of the frame. The left side is ` |
| 176 | `relative_position` | B | A | `The image shows a person walking away from the camera on a sidewalk. To the left of the person (from the viewer’s perspe` |
| 177 | `relative_position` | B | A | `The image shows a wide park pathway with people walking in both directions. On the **right side** of the path (from the ` |
| 179 | `relative_position` | A | B | `The image shows a street scene with buildings, trees, and parked rickshaws. The question asks to choose between “right” ` |
| 180 | `relative_position` | A | B | `The image shows a cityscape with a prominent tall, dark spire on the left side — this is the Scott Monument in Edinburgh` |
| 181 | `relative_position` | A | B | `The image shows a group of cyclists riding on a road in the foreground and middle ground. Above them, there is a raised ` |
| 185 | `relative_position` | A | B | `The image shows a beach scene with people playing volleyball, relaxing, and a small palm tree in a white planter in the ` |
